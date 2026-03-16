import json
import logging
from datetime import date, datetime, timedelta
import anthropic
from config import ANTHROPIC_API_KEY
from database import get_connection

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PROTEIN_GOAL = 180

FOOD_PARSE_PROMPT = """You estimate protein content from food descriptions.

IMPORTANT: Respond with ONLY valid JSON, no other text.

Format:
{
  "foods": [
    {"item": "4 eggs", "protein": 24},
    {"item": "greek yogurt", "protein": 15},
    {"item": "protein shake", "protein": 25}
  ],
  "total_protein": 64
}

Rules:
- Be reasonably accurate with protein estimates (per standard serving sizes)
- Use common nutritional knowledge
- Round to nearest gram
- If unclear portion size, assume a standard serving
- "protein shake" = ~25-30g, "chicken breast" = ~30-35g, "eggs" = ~6g each, "greek yogurt" = ~15-17g per cup
"""

NUTRITION_QUERY_PROMPT = """You determine what nutrition query the user is asking. Respond with ONLY valid JSON:
{
  "query_type": "today_total" | "today_log" | "week_summary" | "average"
}

- "how much protein today" / "protein today" / "how am I doing on protein" → today_total
- "what did I eat today" / "food log" / "meals today" → today_log
- "how was my protein this week" / "protein this week" / "weekly protein" → week_summary
- "what's my protein average" / "average protein" / "protein average" → average
"""


def parse_food(text):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system=FOOD_PARSE_PROMPT,
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


def parse_nutrition_query(text):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=64,
        system=NUTRITION_QUERY_PROMPT,
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


def save_food_entry(description, protein_grams, chat_id):
    conn = get_connection()
    now = datetime.now()
    conn.execute(
        "INSERT INTO nutrition (date, time, description, protein_grams, telegram_chat_id) VALUES (?, ?, ?, ?, ?)",
        (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), description, protein_grams, chat_id),
    )
    conn.commit()
    conn.close()


def get_daily_total(target_date, chat_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(protein_grams), 0) as total FROM nutrition WHERE date=? AND telegram_chat_id=?",
        (target_date, chat_id),
    ).fetchone()
    conn.close()
    return row["total"]


def get_daily_log(target_date, chat_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM nutrition WHERE date=? AND telegram_chat_id=? ORDER BY time",
        (target_date, chat_id),
    ).fetchall()
    conn.close()
    return rows


def get_week_summary(chat_id):
    today = date.today()
    conn = get_connection()
    results = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        row = conn.execute(
            "SELECT COALESCE(SUM(protein_grams), 0) as total FROM nutrition WHERE date=? AND telegram_chat_id=?",
            (d.isoformat(), chat_id),
        ).fetchone()
        results.append((d, row["total"]))
    conn.close()
    return results


def get_average(chat_id):
    today = date.today()
    start = (today - timedelta(days=29)).isoformat()
    conn = get_connection()
    rows = conn.execute(
        "SELECT date, SUM(protein_grams) as total FROM nutrition WHERE date >= ? AND telegram_chat_id=? GROUP BY date",
        (start, chat_id),
    ).fetchall()
    conn.close()

    if not rows:
        return 0, 0
    total = sum(r["total"] for r in rows)
    days = len(rows)
    return round(total / days), days


def format_food_response(data, daily_total):
    foods = data.get("foods", [])
    meal_protein = data.get("total_protein", 0)

    lines = ["🥗 Logged!"]
    for f in foods:
        lines.append(f"  • {f['item']}: ~{f['protein']}g")

    pct = round(daily_total / PROTEIN_GOAL * 100)
    lines.append(f"\nMeal protein: ~{meal_protein}g")
    lines.append(f"Daily total: {daily_total}g / {PROTEIN_GOAL}g ({pct}%)")

    if daily_total >= PROTEIN_GOAL:
        lines.append("\n✅ Goal hit!")
    elif pct >= 70:
        remaining = PROTEIN_GOAL - daily_total
        lines.append(f"\nAlmost there — {remaining}g to go!")

    return "\n".join(lines)


def handle_nutrition_query(query_data, chat_id):
    qt = query_data.get("query_type")
    today = date.today()

    if qt == "today_total":
        total = get_daily_total(today.isoformat(), chat_id)
        pct = round(total / PROTEIN_GOAL * 100)
        remaining = max(0, PROTEIN_GOAL - total)
        status = "✅ Goal hit!" if total >= PROTEIN_GOAL else f"⚠️ {remaining}g to go"
        return f"🥗 Protein today: {total}g / {PROTEIN_GOAL}g ({pct}%)\n{status}"

    elif qt == "today_log":
        entries = get_daily_log(today.isoformat(), chat_id)
        if not entries:
            return "🥗 No food logged today yet."
        total = sum(e["protein_grams"] for e in entries)
        pct = round(total / PROTEIN_GOAL * 100)
        lines = [f"🥗 Food Log — {today.strftime('%A, %B %d')}", ""]
        for e in entries:
            lines.append(f"  {e['time']} — {e['description']} (~{e['protein_grams']}g)")
        lines.append(f"\nTotal: {total}g / {PROTEIN_GOAL}g ({pct}%)")
        return "\n".join(lines)

    elif qt == "week_summary":
        week = get_week_summary(chat_id)
        days_hit = sum(1 for _, t in week if t >= PROTEIN_GOAL)
        lines = [f"🥗 Protein — Last 7 Days ({days_hit}/7 days hit)", ""]
        for d, total in week:
            bar = "█" * min(int(total / PROTEIN_GOAL * 10), 10) + "░" * max(0, 10 - int(total / PROTEIN_GOAL * 10))
            status = "✅" if total >= PROTEIN_GOAL else "❌" if total > 0 else "—"
            lines.append(f"  {d.strftime('%a %m/%d')}: {bar} {total}g {status}")
        return "\n".join(lines)

    elif qt == "average":
        avg, days = get_average(chat_id)
        if days == 0:
            return "🥗 No protein data yet."
        status = "✅ Above goal!" if avg >= PROTEIN_GOAL else f"⚠️ {PROTEIN_GOAL - avg}g below goal on average"
        return f"📊 30-day protein average: {avg}g/day (over {days} days logged)\n{status}"

    return None


def get_protein_check(chat_id):
    """Called by scheduled check-ins. Returns a nudge message or None."""
    today = date.today().isoformat()
    now = datetime.now()
    hour = now.hour
    total = get_daily_total(today, chat_id)

    if hour >= 12 and total == 0:
        return "Hey — don't forget to log your meals today 🥗"
    elif hour >= 18 and total < 100:
        remaining = PROTEIN_GOAL - total
        return f"⚠️ You're at {total}g protein — need {remaining}g more to hit your goal today 💪"
    return None
