import json
import os
import re
from pathlib import Path
import chainlit as cl
from dotenv import load_dotenv
from groq import Groq
from agent import run_agent
from tools.memory import clear_memories
from tools.profile import load_profile, apply_profile_update

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", ".")


def _sanitize_nickname(raw: str) -> str:
    sanitized = re.sub(r"[^a-z0-9_-]", "", raw.strip().lower().replace(" ", "_"))
    return sanitized or "traveler"


def _user_paths(nickname: str) -> tuple[str, str]:
    db_path = f"{DATA_DIR}/db/{nickname}.db"
    profile_path = f"{DATA_DIR}/profiles/{nickname}.json"
    return db_path, profile_path


async def refresh_profile(history: list[dict], profile_path: str) -> None:
    if not history:
        return
    current_profile = load_profile(profile_path)
    formatted = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in history
        if isinstance(m.get("content"), str)
    )
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        max_tokens=512,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are updating a traveler preference profile based on a conversation.\n"
                    "Return ONLY a JSON object — no explanation, no markdown.\n"
                    "Keep all existing fields and values unless the conversation clearly overrides them.\n"
                    "Update values that have changed (e.g. 'actually I hate museums').\n"
                    "Add new top-level keys for preferences discovered that don't fit existing "
                    "categories (e.g. budget, pace, accommodation style, group size).\n"
                    "Do not include trip-specific facts — those are stored separately as memories."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Current profile:\n{json.dumps(current_profile, indent=2)}\n\n"
                    f"Conversation:\n{formatted}"
                ),
            },
        ],
    )
    raw = response.choices[0].message.content or ""
    updated = apply_profile_update(current_profile, raw)
    if updated is not None:
        Path(profile_path).write_text(json.dumps(updated, indent=2))


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])

    res = await cl.AskUserMessage(
        content="Hi! I'm **Chihiro** ✈ What's your name or nickname? I'll use it to remember you across visits.",
        timeout=120,
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return

    nickname = _sanitize_nickname(res["output"])
    db_path, profile_path = _user_paths(nickname)
    cl.user_session.set("db_path", db_path)
    cl.user_session.set("profile_path", profile_path)

    if not Path(profile_path).exists():
        await _run_onboarding(profile_path)
    else:
        await cl.Message(
            content=(
                f"Welcome back, **{nickname}**! I remember you ✈\n\n"
                "Tell me where you're headed and I'll get planning. "
                "Type **/new** any time to start fresh for a new destination."
            )
        ).send()


async def _run_onboarding(profile_path: str):
    await cl.Message(
        content=(
            "Let's set up your profile so I can personalise recommendations. "
            "I'll ask a few quick questions."
        )
    ).send()

    res = await cl.AskUserMessage(
        content="What are your names? (e.g. 'Rafaela and João')", timeout=120
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    names = [n.strip() for n in res["output"].replace(" and ", ",").split(",") if n.strip()]

    res = await cl.AskUserMessage(
        content="What are your main travel interests? (e.g. culture, history, nature, food)",
        timeout=120,
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    interests = [i.strip() for i in res["output"].split(",") if i.strip()]

    res = await cl.AskUserMessage(
        content="What kinds of food do you love? (e.g. local, Japanese, Vietnamese, street food)",
        timeout=120,
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    food = [f.strip() for f in res["output"].split(",") if f.strip()]

    res = await cl.AskUserMessage(
        content="Anything you're NOT into? (e.g. nightlife, spicy food) — or type 'nothing'",
        timeout=120,
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    not_into_raw = res["output"].strip()
    not_into = (
        []
        if not_into_raw.lower() == "nothing"
        else [n.strip() for n in not_into_raw.split(",") if n.strip()]
    )

    profile = {"travelers": names, "interests": interests, "food": food, "not_into": not_into}
    Path(profile_path).parent.mkdir(parents=True, exist_ok=True)
    Path(profile_path).write_text(json.dumps(profile, indent=2))

    await cl.Message(
        content=(
            f"Profile saved! I know you as **{' & '.join(names)}** — "
            f"interested in {', '.join(interests)} with a love for {', '.join(food[:3])} food.\n\n"
            "Now tell me where you're headed and I'll get planning! "
            "Type **/new** any time to start fresh for a new destination."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    db_path = cl.user_session.get("db_path")
    profile_path = cl.user_session.get("profile_path")

    if not db_path or not profile_path:
        await cl.Message(content="Session not initialized. Please refresh the page.").send()
        return

    if message.content.strip() == "/new":
        history = cl.user_session.get("history", [])
        if history and profile_path:
            await refresh_profile(history, profile_path)
        if Path(db_path).exists():
            clear_memories(db_path=db_path)
        cl.user_session.set("history", [])
        await cl.Message(
            content=(
                "Starting fresh! Your profile is saved — I still know your preferences. "
                "Where are we headed next?"
            )
        ).send()
        return

    history = cl.user_session.get("history", [])
    response_text, itinerary_html, updated_history = await run_agent(
        message.content, history=history, profile_path=profile_path, db_path=db_path
    )
    cl.user_session.set("history", updated_history)

    await cl.Message(content=response_text).send()

    if itinerary_html:
        await cl.Message(content=itinerary_html).send()


@cl.on_chat_end
async def on_chat_end():
    history = cl.user_session.get("history", [])
    profile_path = cl.user_session.get("profile_path")
    if history and profile_path:
        await refresh_profile(history, profile_path)
