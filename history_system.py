import sqlite3
from datetime import datetime

class HistorySystem:
    def __init__(self, db_path='users.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_history_table()

    def create_history_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                image_query TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def add_record(self, username, image_query):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO history (username, image_query, generated_at) VALUES (?, ?, ?)
        ''', (username, image_query, now))
        self.conn.commit()

    def get_history(self, username):
        self.cursor.execute('''
            SELECT id, image_query, generated_at FROM history WHERE username = ? ORDER BY generated_at DESC
        ''', (username,))
        return self.cursor.fetchall()

    def delete_record(self, record_id):
        self.cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
        self.conn.commit()

    def get_image_count(self, username):
        self.cursor.execute("SELECT COUNT(*) FROM history WHERE username = ?", (username,))
        return self.cursor.fetchone()[0]
