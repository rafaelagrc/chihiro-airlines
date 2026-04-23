import json

PROFILE_PATH = "profile/interests.json"

def load_profile(path: str = PROFILE_PATH) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def profile_to_prompt(profile: dict) -> str:
    known_keys = {"travelers", "interests", "food", "not_into"}
    travelers = ", ".join(profile.get("travelers", []))
    interests = ", ".join(profile.get("interests", []))
    food = ", ".join(profile.get("food", []))
    not_into = ", ".join(profile.get("not_into", []))
    lines = [
        f"Travelers: {travelers}.",
        f"Interests: {interests}.",
        f"Food preferences: {food}.",
        f"Not interested in: {not_into}.",
    ]
    for key, value in profile.items():
        if key not in known_keys:
            label = key.replace("_", " ").capitalize()
            val = ", ".join(value) if isinstance(value, list) else str(value)
            lines.append(f"{label}: {val}.")
    return "\n".join(lines)
