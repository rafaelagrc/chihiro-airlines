# app.py
import json
import os
from pathlib import Path
import chainlit as cl
from dotenv import load_dotenv
from agent import run_agent
from tools.profile import PROFILE_PATH

load_dotenv()

PROFILE_FILE = Path(PROFILE_PATH)

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    if not PROFILE_FILE.exists():
        await _run_onboarding()
    else:
        await cl.Message(
            content=(
                "Hi! I'm **Chihiro**, your travel planning assistant ✈\n\n"
                "Tell me where you're headed and I'll suggest the best places to stay, "
                "free walking tours, food spots, viewpoints, and experiences tailored to you two."
            )
        ).send()

async def _run_onboarding():
    await cl.Message(
        content=(
            "Welcome! I'm **Chihiro**, your travel planning assistant ✈\n\n"
            "Let's set up your profile so I can personalise recommendations. "
            "I'll ask a few quick questions."
        )
    ).send()

    res = await cl.AskUserMessage(
        content="What are your names? (e.g. 'Rafaela and João')",
        timeout=120
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    names = [n.strip() for n in res["output"].replace(" and ", ",").split(",") if n.strip()]

    res = await cl.AskUserMessage(
        content="What are your main travel interests? (e.g. culture, history, nature, food)",
        timeout=120
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    interests = [i.strip() for i in res["output"].split(",") if i.strip()]

    res = await cl.AskUserMessage(
        content="What kinds of food do you love? (e.g. local, Japanese, Vietnamese, street food)",
        timeout=120
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    food = [f.strip() for f in res["output"].split(",") if f.strip()]

    res = await cl.AskUserMessage(
        content="Anything you're NOT into? (e.g. nightlife, spicy food) — or type 'nothing'",
        timeout=120
    ).send()
    if res is None:
        await cl.Message(content="Setup timed out. Refresh the page to try again.").send()
        return
    not_into_raw = res["output"].strip()
    not_into = [] if not_into_raw.lower() == "nothing" else [n.strip() for n in not_into_raw.split(",") if n.strip()]

    profile = {"travelers": names, "interests": interests, "food": food, "not_into": not_into}
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(profile, indent=2))

    await cl.Message(
        content=(
            f"Profile saved! I know you as **{' & '.join(names)}** — "
            f"interested in {', '.join(interests)} with a love for {', '.join(food[:3])} food.\n\n"
            "Now tell me where you're headed and I'll get planning!"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history", [])
    response_text, itinerary_html, updated_history = await run_agent(message.content, history=history)
    cl.user_session.set("history", updated_history)

    await cl.Message(content=response_text).send()

    if itinerary_html:
        await cl.Message(
            content="",
            elements=[cl.Html(name="itinerary", content=itinerary_html, display="inline")]
        ).send()
