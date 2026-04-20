import json

PROFILE_PATH = "profile/interests.json"

def load_profile(path: str = PROFILE_PATH) -> dict:
    with open(path) as f:
        return json.load(f)

def profile_to_prompt(profile: dict) -> str:
    travelers = ", ".join(profile.get("travelers", []))
    interests = ", ".join(profile.get("interests", []))
    food = ", ".join(profile.get("food", []))
    not_into = ", ".join(profile.get("not_into", []))
    return (
        f"Travelers: {travelers}.\n"
        f"Interests: {interests}.\n"
        f"Food preferences: {food}.\n"
        f"Not interested in: {not_into}."
    )
