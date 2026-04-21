import sqlite3
from db.schema import DB_PATH

def save_memory(fact: str, destination: str | None = None, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO memories (fact, destination) VALUES (?, ?)",
        (fact, destination)
    )
    conn.commit()
    conn.close()

def load_memories(db_path: str = DB_PATH) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT fact, destination, created_at FROM memories ORDER BY id DESC LIMIT 20"
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def clear_memories(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM memories")
    conn.commit()
    conn.close()
