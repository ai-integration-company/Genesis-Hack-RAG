import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()
USER_HISTORY_DB = os.getenv("USER_HISTORY_DB")


def init():
    conn = sqlite3.connect(USER_HISTORY_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_text TEXT,
            bot_reply TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_message(user_id, message_text, bot_reply):
    conn = sqlite3.connect(USER_HISTORY_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (user_id, message_text, bot_reply) VALUES (?, ?, ?)
    ''', (user_id, message_text, bot_reply))
    conn.commit()
    conn.close()


def clear_history(user_id):
    conn = sqlite3.connect(USER_HISTORY_DB)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM messages WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()
