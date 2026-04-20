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
