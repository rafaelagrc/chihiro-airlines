import tempfile
import os
from db.schema import init_db
from tools.memory import save_memory, load_memories, clear_memories

def make_test_db():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    init_db(f.name)
    return f.name

def test_save_memory_stores_fact():
    db_path = make_test_db()
    try:
        save_memory("Loved Nishiki Market", destination="Kyoto", db_path=db_path)
        memories = load_memories(db_path=db_path)
        assert any("Nishiki Market" in m["fact"] for m in memories)
    finally:
        os.unlink(db_path)

def test_save_memory_without_destination():
    db_path = make_test_db()
    try:
        save_memory("Prefer morning visits to busy sites", db_path=db_path)
        memories = load_memories(db_path=db_path)
        assert any("morning visits" in m["fact"] for m in memories)
    finally:
        os.unlink(db_path)

def test_load_memories_returns_most_recent_20():
    db_path = make_test_db()
    try:
        for i in range(25):
            save_memory(f"Memory {i}", db_path=db_path)
        memories = load_memories(db_path=db_path)
        assert len(memories) == 20
        assert memories[0]["fact"] == "Memory 24"
    finally:
        os.unlink(db_path)

def test_load_memories_empty_db():
    db_path = make_test_db()
    try:
        memories = load_memories(db_path=db_path)
        assert memories == []
    finally:
        os.unlink(db_path)

def test_clear_memories_empties_table():
    db_path = make_test_db()
    try:
        save_memory("Loved Nishiki Market", destination="Kyoto", db_path=db_path)
        save_memory("Prefer morning visits", db_path=db_path)
        clear_memories(db_path=db_path)
        assert load_memories(db_path=db_path) == []
    finally:
        os.unlink(db_path)
