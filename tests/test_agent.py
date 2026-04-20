# tests/test_agent.py
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock
from db.schema import init_db
from tools.memory import save_memory

def make_test_db():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    init_db(f.name)
    return f.name

def make_test_profile(tmp_path=None):
    import tempfile, json
    data = {
        "travelers": ["Rafaela", "boyfriend"],
        "interests": ["culture", "history"],
        "food": ["local", "Japanese"],
        "not_into": ["nightlife"]
    }
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name

def test_build_system_prompt_includes_profile():
    from agent import build_system_prompt
    profile_path = make_test_profile()
    db_path = make_test_db()
    try:
        prompt = build_system_prompt(profile_path=profile_path, db_path=db_path)
        assert "culture" in prompt
        assert "Japanese" in prompt
    finally:
        os.unlink(profile_path)
        os.unlink(db_path)

def test_build_system_prompt_includes_memories():
    from agent import build_system_prompt
    profile_path = make_test_profile()
    db_path = make_test_db()
    try:
        save_memory("Loved Nishiki Market", destination="Kyoto", db_path=db_path)
        prompt = build_system_prompt(profile_path=profile_path, db_path=db_path)
        assert "Nishiki Market" in prompt
    finally:
        os.unlink(profile_path)
        os.unlink(db_path)

def test_build_system_prompt_no_memories_section_when_empty():
    from agent import build_system_prompt
    profile_path = make_test_profile()
    db_path = make_test_db()
    try:
        prompt = build_system_prompt(profile_path=profile_path, db_path=db_path)
        assert isinstance(prompt, str)
        assert len(prompt) > 50
    finally:
        os.unlink(profile_path)
        os.unlink(db_path)
