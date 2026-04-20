# tests/test_schema.py
import sqlite3
import tempfile
import os
from db.schema import init_db

def test_init_db_creates_memories_table():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "memories" in tables
        assert "itineraries" in tables
    finally:
        os.unlink(db_path)

def test_init_db_memories_columns():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(memories)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        assert {"id", "fact", "destination", "created_at"} <= columns
    finally:
        os.unlink(db_path)

def test_init_db_is_idempotent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        init_db(db_path)  # calling twice should not raise
    finally:
        os.unlink(db_path)
