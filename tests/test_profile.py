import json
import tempfile
import os
from tools.profile import load_profile, profile_to_prompt

def make_test_profile(data: dict) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name

def test_load_profile_returns_dict():
    path = make_test_profile({"travelers": ["Rafaela"], "interests": ["culture"]})
    try:
        profile = load_profile(path)
        assert profile["travelers"] == ["Rafaela"]
    finally:
        os.unlink(path)

def test_profile_to_prompt_contains_interests():
    profile = {
        "travelers": ["Rafaela", "boyfriend"],
        "interests": ["culture", "history"],
        "food": ["local", "Japanese"],
        "not_into": ["nightlife"]
    }
    prompt = profile_to_prompt(profile)
    assert "culture" in prompt
    assert "Japanese" in prompt
    assert "nightlife" in prompt

def test_profile_to_prompt_is_string():
    profile = {"travelers": [], "interests": [], "food": [], "not_into": []}
    assert isinstance(profile_to_prompt(profile), str)

def test_load_profile_missing_file_returns_empty_dict():
    result = load_profile("/tmp/definitely_does_not_exist_chihiro_abc123.json")
    assert result == {}
