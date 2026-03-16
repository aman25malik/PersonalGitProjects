import sqlite3
from datetime import datetime, date
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message_type TEXT NOT NULL,
            raw_content TEXT NOT NULL,
            parsed_category TEXT,
            parsed_response TEXT,
            telegram_chat_id INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            day_type TEXT NOT NULL,
            notes TEXT,
            duration_mins INTEGER,
            did_abs INTEGER DEFAULT 0,
            raw_input TEXT,
            telegram_chat_id INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            exercise TEXT NOT NULL,
            sets INTEGER NOT NULL DEFAULT 1,
            reps INTEGER NOT NULL DEFAULT 0,
            weight REAL NOT NULL DEFAULT 0,
            is_pr INTEGER DEFAULT 0,
            FOREIGN KEY (workout_id) REFERENCES workouts(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nutrition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            description TEXT NOT NULL,
            protein_grams INTEGER NOT NULL DEFAULT 0,
            telegram_chat_id INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            due_date TEXT,
            due_time TEXT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            raw_input TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            item_type TEXT NOT NULL DEFAULT 'task',
            telegram_chat_id INTEGER
        )
    """)
    conn.commit()
    conn.close()


def save_message(message_type, raw_content, parsed_category, parsed_response, chat_id):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO messages (timestamp, message_type, raw_content, parsed_category, parsed_response, telegram_chat_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (datetime.now().isoformat(), message_type, raw_content, parsed_category, parsed_response, chat_id),
    )
    conn.commit()
    conn.close()


def save_task(title, category, due_date, due_time, priority, item_type, raw_input, chat_id):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO tasks (created_at, due_date, due_time, title, category, status, raw_input, priority, item_type, telegram_chat_id)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        """,
        (datetime.now().isoformat(), due_date, due_time, title, category, raw_input, priority, item_type, chat_id),
    )
    conn.commit()
    conn.close()


def complete_task(title_query, chat_id):
    conn = get_connection()
    task = conn.execute(
        "SELECT id, title FROM tasks WHERE status='pending' AND telegram_chat_id=? AND LOWER(title) LIKE ? ORDER BY created_at DESC LIMIT 1",
        (chat_id, f"%{title_query.lower()}%"),
    ).fetchone()
    if task:
        conn.execute("UPDATE tasks SET status='done' WHERE id=?", (task["id"],))
        conn.commit()
        conn.close()
        return task["title"]
    conn.close()
    return None


def drop_task(title_query, chat_id):
    conn = get_connection()
    task = conn.execute(
        "SELECT id, title FROM tasks WHERE status='pending' AND telegram_chat_id=? AND LOWER(title) LIKE ? ORDER BY created_at DESC LIMIT 1",
        (chat_id, f"%{title_query.lower()}%"),
    ).fetchone()
    if task:
        conn.execute("UPDATE tasks SET status='dropped' WHERE id=?", (task["id"],))
        conn.commit()
        conn.close()
        return task["title"]
    conn.close()
    return None


def get_tasks_by_date(target_date, chat_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE status='pending' AND telegram_chat_id=? AND due_date=? ORDER BY due_time, priority",
        (chat_id, target_date),
    ).fetchall()
    conn.close()
    return rows


def get_tasks_by_date_range(start_date, end_date, chat_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE status='pending' AND telegram_chat_id=? AND due_date BETWEEN ? AND ? ORDER BY due_date, due_time",
        (chat_id, start_date, end_date),
    ).fetchall()
    conn.close()
    return rows


def get_tasks_by_category(category, chat_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE status='pending' AND telegram_chat_id=? AND LOWER(category)=? ORDER BY due_date, priority",
        (chat_id, category.lower()),
    ).fetchall()
    conn.close()
    return rows


def get_overdue_tasks(chat_id):
    today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE status='pending' AND telegram_chat_id=? AND due_date < ? AND due_date IS NOT NULL ORDER BY due_date",
        (chat_id, today),
    ).fetchall()
    conn.close()
    return rows


def get_all_pending_tasks(chat_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE status='pending' AND telegram_chat_id=? ORDER BY category, due_date, priority",
        (chat_id,),
    ).fetchall()
    conn.close()
    return rows


def recategorize_last_task(new_category, chat_id):
    conn = get_connection()
    task = conn.execute(
        "SELECT id, title, category FROM tasks WHERE telegram_chat_id=? ORDER BY created_at DESC LIMIT 1",
        (chat_id,),
    ).fetchone()
    if task:
        conn.execute("UPDATE tasks SET category=? WHERE id=?", (new_category, task["id"]))
        conn.commit()
        old_cat = task["category"]
        title = task["title"]
        conn.close()
        return title, old_cat
    conn.close()
    return None, None
