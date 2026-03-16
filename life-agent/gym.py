import json
import logging
from datetime import date, timedelta, datetime
import anthropic
from config import ANTHROPIC_API_KEY
from database import get_connection

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SPLIT = [
    "Chest & Back",
    "Legs",
    "Shoulders & Arms",
    "Chest, Back & Triceps",
]

WORKOUT_PARSE_PROMPT = """You parse gym workout logs into structured JSON.

IMPORTANT: Respond with ONLY valid JSON, no other text.

Today's date is: {today}

Format:
{{
  "day_type": "Chest & Back" | "Legs" | "Shoulders & Arms" | "Chest, Back & Triceps",
  "exercises": [
    {{"exercise": "Bench Press", "sets": 3, "reps": 5, "weight": 185}},
    {{"exercise": "Pull-ups", "sets": 3, "reps": 8, "weight": 0}}
  ],
  "did_abs": true/false,
  "notes": "any extra notes from the message or null",
  "duration_mins": estimated duration in minutes or null
}}

Rules:
- "185x5" means weight=185, reps=5, assume sets=1 unless stated (e.g. "3x8" with a weight means sets=3 reps=8)
- "3x8" without a weight before it means sets=3, reps=8, weight=0 (bodyweight)
- If format is "bench 185x5" that's 1 set of 5 at 185
- If format is "bench 3x5 at 185" or "bench 185 3x5" that's 3 sets of 5 at 185
- Detect day_type from exercises mentioned or if user states it directly
- did_abs = true if user mentions abs, core, planks, crunches, etc.
- Normalize exercise names: "bench" = "Bench Press", "squat" = "Squat", "dl" or "deadlift" = "Deadlift", etc.
"""

GYM_QUERY_PROMPT = """You determine what gym query the user is asking. Respond with ONLY valid JSON:
{{
  "query_type": "last_session" | "exercise_pr" | "week_count" | "day_history" | "consistency" | "all_prs" | "suggest_next",
  "day_type": "specific day type if asking about a day, otherwise null",
  "exercise": "specific exercise name if asking about one, otherwise null"
}}

- "what did I do last chest day" → last_session, day_type="Chest & Back"
- "what's my bench PR" / "bench press PR" → exercise_pr, exercise="Bench Press"
- "how many times did I lift this week" → week_count
- "show my leg progress" → day_history, day_type="Legs"
- "am I hitting 4 days a week" → consistency
- "what are all my PRs" / "show PRs" → all_prs
- "what should I train today" / "what should I do today" → suggest_next

Normalize exercise names: bench = Bench Press, squat = Squat, deadlift = Deadlift, ohp = Overhead Press, rows = Bent Over Rows, etc.
Day types: "Chest & Back", "Legs", "Shoulders & Arms", "Chest, Back & Triceps"
"""


def parse_workout(text):
    today = date.today().isoformat()
    prompt = WORKOUT_PARSE_PROMPT.replace("{today}", today)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=prompt,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
        else:
            return None
    return data


def parse_gym_query(text):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        system=GYM_QUERY_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
        else:
            return None
    return data


def save_workout(data, raw_input, chat_id):
    conn = get_connection()
    today = date.today().isoformat()

    is_baseline = not has_previous_workouts(conn, chat_id)

    cursor = conn.execute(
        "INSERT INTO workouts (date, day_type, notes, duration_mins, did_abs, raw_input, telegram_chat_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (today, data["day_type"], data.get("notes"), data.get("duration_mins"), data.get("did_abs", False), raw_input, chat_id),
    )
    workout_id = cursor.lastrowid

    prs = []

    for ex in data.get("exercises", []):
        exercise = ex["exercise"]
        weight = ex.get("weight", 0)
        is_pr = False

        if weight > 0 and not is_baseline:
            prev_max = conn.execute(
                "SELECT MAX(weight) as max_w FROM sets WHERE exercise=? AND weight > 0 AND workout_id IN (SELECT id FROM workouts WHERE telegram_chat_id=?)",
                (exercise, chat_id),
            ).fetchone()
            if prev_max and (prev_max["max_w"] is None or weight > prev_max["max_w"]):
                is_pr = True
                prs.append({"exercise": exercise, "weight": weight})

        conn.execute(
            "INSERT INTO sets (workout_id, exercise, sets, reps, weight, is_pr) VALUES (?, ?, ?, ?, ?, ?)",
            (workout_id, exercise, ex.get("sets", 1), ex.get("reps", 0), weight, is_pr),
        )

    conn.commit()
    conn.close()
    return workout_id, prs, is_baseline


def has_previous_workouts(conn, chat_id):
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM workouts WHERE telegram_chat_id=?",
        (chat_id,),
    ).fetchone()
    return row["cnt"] > 0


def format_workout_response(data, prs, is_baseline):
    lines = [f"💪 {data['day_type']} — Logged!"]
    if is_baseline:
        lines.append("📊 Baseline session recorded. Future sessions will compare against this.")
    lines.append("")

    for ex in data.get("exercises", []):
        weight_str = f" @ {ex['weight']}lbs" if ex.get("weight", 0) > 0 else " (bodyweight)"
        pr_flag = ""
        for pr in prs:
            if pr["exercise"] == ex["exercise"]:
                pr_flag = " 🏆 NEW PR!"
                break
        lines.append(f"  • {ex['exercise']}: {ex.get('sets', 1)}x{ex.get('reps', 0)}{weight_str}{pr_flag}")

    if data.get("did_abs"):
        lines.append("\n  ✔️ Abs work logged")
    if data.get("notes"):
        lines.append(f"\n  📝 {data['notes']}")

    return "\n".join(lines)


def get_suggest_next(chat_id):
    conn = get_connection()
    last = conn.execute(
        "SELECT day_type, date FROM workouts WHERE telegram_chat_id=? ORDER BY date DESC, id DESC LIMIT 1",
        (chat_id,),
    ).fetchone()
    conn.close()

    if not last:
        return f"💪 No workouts logged yet. Start with {SPLIT[0]}!"

    last_type = last["day_type"]
    last_date = last["date"]
    days_since = (date.today() - date.fromisoformat(last_date)).days

    try:
        idx = SPLIT.index(last_type)
        next_idx = (idx + 1) % len(SPLIT)
    except ValueError:
        next_idx = 0

    next_day = SPLIT[next_idx]
    nudge = ""
    if days_since >= 2:
        nudge = f"\n\n⚡ It's been {days_since} days since your last session — time to get after it!"

    return f"💪 Next up: {next_day}{nudge}"


def get_last_session(day_type, chat_id):
    conn = get_connection()
    workout = conn.execute(
        "SELECT * FROM workouts WHERE telegram_chat_id=? AND LOWER(day_type) LIKE ? ORDER BY date DESC LIMIT 1",
        (chat_id, f"%{day_type.lower()}%"),
    ).fetchone()
    if not workout:
        conn.close()
        return f"📊 No {day_type} sessions found yet."

    sets = conn.execute(
        "SELECT * FROM sets WHERE workout_id=?", (workout["id"],)
    ).fetchall()
    conn.close()

    lines = [f"💪 Last {workout['day_type']} — {workout['date']}", ""]
    for s in sets:
        weight_str = f" @ {s['weight']}lbs" if s["weight"] > 0 else " (bodyweight)"
        pr_flag = " 🏆 PR" if s["is_pr"] else ""
        lines.append(f"  • {s['exercise']}: {s['sets']}x{s['reps']}{weight_str}{pr_flag}")

    return "\n".join(lines)


def get_exercise_pr(exercise, chat_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT exercise, MAX(weight) as max_w, reps FROM sets WHERE LOWER(exercise) LIKE ? AND weight > 0 AND workout_id IN (SELECT id FROM workouts WHERE telegram_chat_id=?) ORDER BY weight DESC LIMIT 1",
        (f"%{exercise.lower()}%", chat_id),
    ).fetchone()
    conn.close()

    if not row or row["max_w"] is None:
        return f"📊 No {exercise} data logged yet."

    return f"🏆 {row['exercise']} PR: {row['max_w']}lbs x {row['reps']}"


def get_week_count(chat_id):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM workouts WHERE telegram_chat_id=? AND date >= ?",
        (chat_id, monday.isoformat()),
    ).fetchone()
    conn.close()

    count = row["cnt"]
    goal_status = "✅ On track!" if count >= 4 else f"{'🟡' if count >= 2 else '🔴'} {4 - count} more to hit your 4x/week goal"
    return f"📊 Lifting sessions this week: {count}/4\n{goal_status}"


def get_consistency(chat_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT date FROM workouts WHERE telegram_chat_id=? ORDER BY date DESC LIMIT 28",
        (chat_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return "📊 No workout history yet."

    today = date.today()
    weeks = {}
    for r in rows:
        d = date.fromisoformat(r["date"])
        week_start = d - timedelta(days=d.weekday())
        key = week_start.isoformat()
        weeks[key] = weeks.get(key, 0) + 1

    lines = ["📊 Weekly Consistency (last 4 weeks)", ""]
    for week_start in sorted(weeks.keys(), reverse=True)[:4]:
        count = weeks[week_start]
        bar = "█" * count + "░" * (4 - min(count, 4))
        status = "✅" if count >= 4 else "❌"
        lines.append(f"  {week_start}: {bar} {count}/4 {status}")

    return "\n".join(lines)


def get_all_prs(chat_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT exercise, MAX(weight) as max_w, reps FROM sets
           WHERE is_pr=1 AND workout_id IN (SELECT id FROM workouts WHERE telegram_chat_id=?)
           GROUP BY exercise ORDER BY exercise""",
        (chat_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return "🏆 No PRs recorded yet. Log your baseline session first!"

    lines = ["🏆 All Personal Records", ""]
    for r in rows:
        lines.append(f"  • {r['exercise']}: {r['max_w']}lbs x {r['reps']}")

    return "\n".join(lines)


def handle_gym_query(query_data, chat_id):
    qt = query_data.get("query_type")

    if qt == "suggest_next":
        return get_suggest_next(chat_id)
    elif qt == "last_session":
        day_type = query_data.get("day_type", "")
        return get_last_session(day_type, chat_id)
    elif qt == "exercise_pr":
        exercise = query_data.get("exercise", "")
        return get_exercise_pr(exercise, chat_id)
    elif qt == "week_count":
        return get_week_count(chat_id)
    elif qt == "day_history":
        day_type = query_data.get("day_type", "")
        return get_last_session(day_type, chat_id)
    elif qt == "consistency":
        return get_consistency(chat_id)
    elif qt == "all_prs":
        return get_all_prs(chat_id)

    return None
