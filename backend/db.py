import os
import re
import sqlite3

from requests import get

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.getenv("DB_NAME", "chat.db")
)

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 10000')
    return conn



def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '새 대화',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


def create_session(title='새 대화'):
    conn = get_conn()
    cur = conn.execute("INSERT INTO sessions (title) VALUES (?)", (title,))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

#Read
def read_sessions():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

#Create
def create_message(session_id, role, text):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO messages (session_id, role, text) VALUES (?, ?, ?)",
        (session_id, role, text),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

#Read
def read_messages(session_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def count_messages(session_id):
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) AS n FROM messages WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    return count["n"] if count else 0


def update_session(session_id, title):
    conn = get_conn()
    conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
    conn.commit()
    conn.close()
    return session_id

#Delete
def delete_session(session_id):
    conn = get_conn()
    cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed