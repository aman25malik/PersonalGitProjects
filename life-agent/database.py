import sqlite3
from datetime import datetime
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
