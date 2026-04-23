---
title: Chihiro Airlines
emoji: ✈️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Chihiro Airlines ✈

A personal AI travel assistant that knows your interests and helps you plan vacations — finding the best places to stay, free walking tours, local food spots, viewpoints, and experiences.

## What it does

- **Personalised recommendations** — knows your travel style, food preferences, and past trips
- **Live web search** — always fetches current info for walking tours, opening hours, and time-sensitive details
- **Itinerary builder** — turn a conversation into a structured day-by-day plan rendered in the UI
- **Travel memory** — remembers notable places and preferences across sessions

## Stack

| | |
|---|---|
| UI | [Chainlit](https://chainlit.io) |
| AI | [Groq](https://groq.com) — `llama-3.3-70b-versatile` |
| Search | [Tavily](https://tavily.com) |
| Memory | SQLite |
| Package manager | [uv](https://docs.astral.sh/uv/) |

## Setup

**1. Get API keys (both free)**
- Groq: [console.groq.com](https://console.groq.com) → API Keys
- Tavily: [tavily.com](https://tavily.com) → free tier (1000 searches/month)

**2. Install dependencies**
```bash
uv sync
```

**3. Configure environment**
```bash
cp .env.example .env
# edit .env and fill in your keys
```

**4. Run**
```bash
uv run chainlit run app.py
```

Open [http://localhost:8000](http://localhost:8000). On first launch, Chihiro will ask a few questions to set up your profile.

## Project structure

```
├── app.py              # Chainlit entry point + onboarding
├── agent.py            # Groq tool-calling loop
├── tools/
│   ├── search.py       # Tavily web search
│   ├── memory.py       # Save/load memories from SQLite
│   ├── itinerary.py    # Build + render itinerary HTML
│   └── profile.py      # Load interest profile
├── db/
│   └── schema.py       # SQLite schema
├── profile/
│   └── interests.json  # Your travel interests (edit freely)
└── tests/              # pytest test suite
```

## Customising your profile

Edit `profile/interests.json` at any time:

```json
{
  "travelers": ["Rafaela", "boyfriend"],
  "interests": ["culture", "history", "viewpoints", "nature parks"],
  "food": ["local", "street food", "Japanese", "Vietnamese", "Indian", "Italian"],
  "not_into": ["nightlife"]
}
```

## Tests

```bash
uv run pytest
```

## Deploying to Hugging Face Spaces

1. Create a new Space at huggingface.co/new-space — SDK: **Docker**, Visibility: **Public**
2. In Space **Settings → Storage**, click **Enable Persistent Storage**
3. In Space **Settings → Variables and secrets**, add:
   - `GROQ_API_KEY` — your Groq key (mark as **secret**)
   - `TAVILY_API_KEY` — your Tavily key (mark as **secret**)
   - `DATA_DIR` — value `/data` (plain variable)
4. Push to the Space's git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/chihiro-airlines
   git push space main
   ```
5. The Space builds automatically. Share the URL — anyone can use it.

Each visitor picks a nickname on first visit. Their profile and memories are stored in `/data/` and survive restarts and redeployments.
