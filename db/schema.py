# db/schema.py
import sqlite3

DB_PATH = "db/chihiro.db"

def init_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            destination TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS itineraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            days_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
