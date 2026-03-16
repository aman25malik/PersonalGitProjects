import os
import sqlite3
from datetime import date, timedelta, datetime
from flask import Flask, jsonify

DB_PATH = os.path.join(os.getenv("DATA_DIR", os.path.dirname(__file__)), "life_agent.db")

app = Flask(__name__)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def safe_query(query, params=()):
    try:
        conn = get_conn()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


@app.route("/")
def index():
    return DASHBOARD_HTML


@app.route("/api/data")
def api_data():
    today = date.today()
    thirty_days_ago = (today - timedelta(days=29)).isoformat()
    eight_weeks_ago = (today - timedelta(weeks=8)).isoformat()
    seven_days_ago = (today - timedelta(days=6)).isoformat()

    # --- GYM METRICS ---
    # Top exercises weight progression
    top_exercises = safe_query(
        "SELECT exercise, COUNT(*) as cnt FROM sets GROUP BY exercise ORDER BY cnt DESC LIMIT 5"
    )
    weight_progression = {}
    for ex in top_exercises:
        name = ex["exercise"]
        rows = safe_query(
            """SELECT w.date, MAX(s.weight) as max_weight FROM sets s
               JOIN workouts w ON s.workout_id = w.id
               WHERE s.exercise=? AND s.weight > 0
               GROUP BY w.date ORDER BY w.date""",
            (name,),
        )
        weight_progression[name] = rows

    # Weekly workout frequency (last 8 weeks)
    workout_weeks = []
    for i in range(7, -1, -1):
        week_start = today - timedelta(weeks=i, days=today.weekday())
        week_end = week_start + timedelta(days=6)
        rows = safe_query(
            "SELECT COUNT(*) as cnt FROM workouts WHERE date BETWEEN ? AND ?",
            (week_start.isoformat(), week_end.isoformat()),
        )
        workout_weeks.append({
            "label": week_start.strftime("%b %d"),
            "count": rows[0]["cnt"] if rows else 0,
        })

    # Current PRs
    prs = safe_query(
        """SELECT s.exercise, MAX(s.weight) as weight, s.reps, w.date
           FROM sets s JOIN workouts w ON s.workout_id = w.id
           WHERE s.weight > 0
           GROUP BY s.exercise ORDER BY s.weight DESC"""
    )

    # Workout streak
    streak_rows = safe_query("SELECT DISTINCT date FROM workouts ORDER BY date DESC")
    current_streak = 0
    if streak_rows:
        d = today
        dates_set = {r["date"] for r in streak_rows}
        while d.isoformat() in dates_set or (d == today and today.isoformat() not in dates_set):
            if d.isoformat() in dates_set:
                current_streak += 1
            elif d != today:
                break
            d -= timedelta(days=1)

    # --- PROTEIN METRICS ---
    # Daily protein last 30 days
    protein_days = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        rows = safe_query(
            "SELECT COALESCE(SUM(protein_grams), 0) as total FROM nutrition WHERE date=?",
            (d.isoformat(),),
        )
        total = rows[0]["total"] if rows else 0
        protein_days.append({"date": d.strftime("%m/%d"), "total": total, "hit": total >= 180})

    # Goal hit rates
    last_7 = [p for p in protein_days[-7:] if p["total"] > 0]
    last_30 = [p for p in protein_days if p["total"] > 0]
    hit_7 = sum(1 for p in last_7 if p["hit"]) / max(len(last_7), 1) * 100
    hit_30 = sum(1 for p in last_30 if p["hit"]) / max(len(last_30), 1) * 100

    # 30 day average
    logged_totals = [p["total"] for p in protein_days if p["total"] > 0]
    avg_30 = round(sum(logged_totals) / max(len(logged_totals), 1))

    # Today's protein
    today_protein = safe_query(
        "SELECT COALESCE(SUM(protein_grams), 0) as total FROM nutrition WHERE date=?",
        (today.isoformat(),),
    )
    protein_today = today_protein[0]["total"] if today_protein else 0

    # --- TASK METRICS ---
    # Completion rate by category
    task_completion = safe_query(
        """SELECT category, status, COUNT(*) as cnt FROM tasks
           WHERE created_at >= ? GROUP BY category, status""",
        (thirty_days_ago,),
    )

    # Tasks completed this week vs last week
    this_week_start = (today - timedelta(days=today.weekday())).isoformat()
    last_week_start = (today - timedelta(days=today.weekday() + 7)).isoformat()
    last_week_end = (today - timedelta(days=today.weekday() + 1)).isoformat()

    this_week_done = safe_query(
        "SELECT COUNT(*) as cnt FROM tasks WHERE status='done' AND created_at >= ?",
        (this_week_start,),
    )
    last_week_done = safe_query(
        "SELECT COUNT(*) as cnt FROM tasks WHERE status='done' AND created_at BETWEEN ? AND ?",
        (last_week_start, last_week_end),
    )

    # Overdue
    overdue = safe_query(
        "SELECT COUNT(*) as cnt FROM tasks WHERE status='pending' AND due_date < ? AND due_date IS NOT NULL",
        (today.isoformat(),),
    )

    # Most productive category
    top_category = safe_query(
        """SELECT category, COUNT(*) as cnt FROM tasks
           WHERE status='done' AND created_at >= ?
           GROUP BY category ORDER BY cnt DESC LIMIT 1""",
        (thirty_days_ago,),
    )

    return jsonify({
        "greeting": get_greeting(),
        "updated": datetime.now().strftime("%I:%M %p"),
        "gym": {
            "weight_progression": weight_progression,
            "workout_weeks": workout_weeks,
            "prs": prs,
            "current_streak": current_streak,
        },
        "protein": {
            "daily": protein_days,
            "hit_rate_7": round(hit_7),
            "hit_rate_30": round(hit_30),
            "avg_30": avg_30,
            "today": protein_today,
        },
        "tasks": {
            "completion": task_completion,
            "this_week": this_week_done[0]["cnt"] if this_week_done else 0,
            "last_week": last_week_done[0]["cnt"] if last_week_done else 0,
            "overdue": overdue[0]["cnt"] if overdue else 0,
            "top_category": top_category[0] if top_category else None,
        },
    })


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Life Agent Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0a; color: #e5e5e5; font-family: Inter, -apple-system, system-ui, sans-serif; padding: 20px; }
  .header { text-align: center; margin-bottom: 30px; }
  .header h1 { font-size: 28px; color: #fff; }
  .header .subtitle { color: #666; font-size: 14px; margin-top: 4px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; max-width: 1400px; margin: 0 auto; }
  .card { background: #111; border: 1px solid #222; border-radius: 12px; padding: 20px; }
  .card h2 { font-size: 16px; color: #888; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
  .big-number { font-size: 48px; font-weight: 700; color: #3b82f6; }
  .big-number .unit { font-size: 20px; color: #666; }
  .big-number.success { color: #10b981; }
  .big-number.warning { color: #ef4444; }
  .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1a1a1a; }
  .stat-row:last-child { border: none; }
  .stat-label { color: #888; }
  .stat-value { color: #fff; font-weight: 600; }
  .stat-value.gold { color: #f59e0b; }
  .stat-value.red { color: #ef4444; }
  .pr-badge { color: #f59e0b; font-size: 12px; margin-left: 4px; }
  canvas { max-height: 250px; }
  .section-title { font-size: 20px; color: #fff; margin: 30px 0 16px; padding-left: 8px; border-left: 3px solid #3b82f6; }
  .section-title:first-of-type { margin-top: 0; }
  @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } body { padding: 12px; } .big-number { font-size: 36px; } }
</style>
</head>
<body>
<div class="header">
  <h1 id="greeting">Loading...</h1>
  <div class="subtitle">Last updated: <span id="updated">—</span></div>
</div>

<div class="section-title">💪 Gym</div>
<div class="grid">
  <div class="card"><h2>Weight Progression</h2><canvas id="weightChart"></canvas></div>
  <div class="card"><h2>Weekly Frequency</h2><canvas id="freqChart"></canvas></div>
  <div class="card"><h2>Current PRs</h2><div id="prTable"></div></div>
  <div class="card"><h2>Workout Streak</h2><div class="big-number" id="streak">0</div><p style="color:#666;margin-top:4px">consecutive days</p></div>
</div>

<div class="section-title">🥗 Protein</div>
<div class="grid">
  <div class="card" style="grid-column: span 2"><h2>Daily Protein (30 days)</h2><canvas id="proteinChart"></canvas></div>
  <div class="card"><h2>Today's Protein</h2><div class="big-number" id="proteinToday">0<span class="unit">g / 180g</span></div><div id="proteinBar" style="margin-top:12px;background:#1a1a1a;border-radius:6px;height:12px;overflow:hidden"><div id="proteinFill" style="height:100%;border-radius:6px;transition:width 1s"></div></div></div>
  <div class="card"><h2>Goal Hit Rate</h2><div id="hitRates"></div></div>
</div>

<div class="section-title">✅ Tasks</div>
<div class="grid">
  <div class="card"><h2>Completion by Category</h2><canvas id="taskChart"></canvas></div>
  <div class="card"><h2>Task Stats</h2><div id="taskStats"></div></div>
</div>

<script>
const COLORS = { blue: '#3b82f6', green: '#10b981', red: '#ef4444', gold: '#f59e0b', gray: '#666' };
const CHART_COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#666'];
Chart.defaults.color = '#888';
Chart.defaults.borderColor = '#1a1a1a';

let charts = {};

async function loadData() {
  const resp = await fetch('/api/data');
  const d = await resp.json();

  document.getElementById('greeting').textContent = d.greeting + ', Aman';
  document.getElementById('updated').textContent = d.updated;

  // Streak
  document.getElementById('streak').innerHTML = d.gym.current_streak + '<span class="unit"> days</span>';

  // Weight progression
  if (charts.weight) charts.weight.destroy();
  const wpLabels = [...new Set(Object.values(d.gym.weight_progression).flatMap(v => v.map(r => r.date)))].sort();
  const wpDatasets = Object.entries(d.gym.weight_progression).map(([name, rows], i) => ({
    label: name, data: wpLabels.map(l => { const r = rows.find(x => x.date === l); return r ? r.max_weight : null; }),
    borderColor: CHART_COLORS[i % CHART_COLORS.length], tension: 0.3, spanGaps: true, pointRadius: 3,
  }));
  charts.weight = new Chart(document.getElementById('weightChart'), {
    type: 'line', data: { labels: wpLabels.map(l => l.slice(5)), datasets: wpDatasets },
    options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }, scales: { y: { title: { display: true, text: 'lbs' } } } }
  });

  // Weekly frequency
  if (charts.freq) charts.freq.destroy();
  charts.freq = new Chart(document.getElementById('freqChart'), {
    type: 'bar', data: { labels: d.gym.workout_weeks.map(w => w.label),
      datasets: [{ data: d.gym.workout_weeks.map(w => w.count), backgroundColor: d.gym.workout_weeks.map(w => w.count >= 4 ? COLORS.green : COLORS.blue), borderRadius: 4 }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
  });

  // PRs table
  document.getElementById('prTable').innerHTML = d.gym.prs.length ? d.gym.prs.map(p =>
    '<div class="stat-row"><span class="stat-label">' + p.exercise + '</span><span class="stat-value gold">' + p.weight + 'lbs x' + p.reps + '</span></div>'
  ).join('') : '<p style="color:#666">No PRs yet</p>';

  // Protein chart
  if (charts.protein) charts.protein.destroy();
  charts.protein = new Chart(document.getElementById('proteinChart'), {
    type: 'bar', data: { labels: d.protein.daily.map(p => p.date),
      datasets: [{ data: d.protein.daily.map(p => p.total), backgroundColor: d.protein.daily.map(p => p.total >= 180 ? COLORS.green : p.total > 0 ? COLORS.red : '#1a1a1a'), borderRadius: 2 }] },
    options: { responsive: true, plugins: { legend: { display: false }, annotation: {} }, scales: { y: { beginAtZero: true } } }
  });

  // Today's protein
  const pt = d.protein.today;
  const pct = Math.min(Math.round(pt / 180 * 100), 100);
  document.getElementById('proteinToday').innerHTML = pt + '<span class="unit">g / 180g</span>';
  document.getElementById('proteinToday').className = 'big-number ' + (pt >= 180 ? 'success' : pt >= 100 ? '' : 'warning');
  document.getElementById('proteinFill').style.width = pct + '%';
  document.getElementById('proteinFill').style.background = pt >= 180 ? COLORS.green : pt >= 100 ? COLORS.blue : COLORS.red;

  // Hit rates
  document.getElementById('hitRates').innerHTML =
    '<div class="stat-row"><span class="stat-label">Last 7 days</span><span class="stat-value">' + d.protein.hit_rate_7 + '%</span></div>' +
    '<div class="stat-row"><span class="stat-label">Last 30 days</span><span class="stat-value">' + d.protein.hit_rate_30 + '%</span></div>' +
    '<div class="stat-row"><span class="stat-label">30-day avg</span><span class="stat-value">' + d.protein.avg_30 + 'g</span></div>';

  // Task completion donut
  if (charts.task) charts.task.destroy();
  const catCounts = {};
  d.tasks.completion.filter(t => t.status === 'done').forEach(t => { catCounts[t.category] = (catCounts[t.category] || 0) + t.cnt; });
  const cats = Object.keys(catCounts);
  if (cats.length) {
    charts.task = new Chart(document.getElementById('taskChart'), {
      type: 'doughnut', data: { labels: cats, datasets: [{ data: cats.map(c => catCounts[c]), backgroundColor: CHART_COLORS.slice(0, cats.length), borderWidth: 0 }] },
      options: { responsive: true, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } } }
    });
  } else {
    document.getElementById('taskChart').parentElement.innerHTML += '<p style="color:#666;text-align:center">No completed tasks yet</p>';
  }

  // Task stats
  document.getElementById('taskStats').innerHTML =
    '<div class="stat-row"><span class="stat-label">Completed this week</span><span class="stat-value">' + d.tasks.this_week + '</span></div>' +
    '<div class="stat-row"><span class="stat-label">Completed last week</span><span class="stat-value">' + d.tasks.last_week + '</span></div>' +
    '<div class="stat-row"><span class="stat-label">Overdue tasks</span><span class="stat-value ' + (d.tasks.overdue > 0 ? 'red' : '') + '">' + d.tasks.overdue + '</span></div>' +
    '<div class="stat-row"><span class="stat-label">Top category (30d)</span><span class="stat-value">' + (d.tasks.top_category ? d.tasks.top_category.category + ' (' + d.tasks.top_category.cnt + ')' : '—') + '</span></div>';
}

loadData();
setInterval(loadData, 60000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
