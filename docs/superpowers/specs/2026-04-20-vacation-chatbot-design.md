# Vacation Chatbot — Design Spec
_2026-04-20_

## Overview

A web-based AI chatbot that helps Rafaela and her boyfriend plan vacations. It knows their interests and travel style, recommends places to stay, free walking tours, food spots, viewpoints, and experiences. Supports both conversational Q&A and structured itinerary building.

---

## User Profile

**Travelers:** Rafaela + boyfriend

**Interests:** Culture, history, viewpoints, natural parks

**Food:** Local food, street food, food courts, Japanese, Vietnamese, Indian, Italian, Chinese, Thai

**Not into:** Nightlife

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  UI: Chainlit chat + custom itinerary panel  │
├─────────────────────────────────────────────┤
│  Agent: Claude (claude-sonnet-4-6)           │
│    ↳ tools: web_search, save_memory,         │
│             build_itinerary                  │
├─────────────────────────────────────────────┤
│  Search: Tavily API (triggered on demand)    │
├─────────────────────────────────────────────┤
│  Memory: SQLite                              │
│    ↳ tables: profile, memories, itineraries  │
└─────────────────────────────────────────────┘
```

Every conversation injects the user profile + last 20 memories into Claude's system prompt as context.

---

## File Structure

```
chihiro-airlines/
├── app.py                  # Chainlit entry point
├── agent.py                # Claude API calls + tool routing
├── tools/
│   ├── search.py           # Tavily web search tool
│   ├── memory.py           # save/load memories from SQLite
│   └── itinerary.py        # build + update structured itinerary
├── db/
│   └── chihiro.db          # SQLite: profile, memories, itineraries
├── profile/
│   └── interests.json      # static interest profile (editable)
├── ui/
│   └── itinerary_panel.py  # Chainlit custom element for itinerary view
└── pyproject.toml
```

---

## Profile Format

`profile/interests.json`:
```json
{
  "travelers": ["Rafaela", "boyfriend"],
  "interests": ["culture", "history", "viewpoints", "nature parks"],
  "food": ["local", "street food", "Japanese", "Vietnamese", "Indian", "Italian", "Chinese", "Thai", "food courts"],
  "not_into": ["nightlife"]
}
```

---

## Agent Tools

### `web_search(query: str) → str`
Calls Tavily API. Triggered when Claude needs fresh info:
- Free walking tours (always searched — schedules change)
- Opening hours or current status
- "Best X in Y right now" queries
- Any time-sensitive information

Claude answers from built-in knowledge first; searches only when knowledge may be stale or insufficient.

### `save_memory(fact: str, destination: str | None) → None`
Saves a notable preference or experience to SQLite `memories` table. Example:
> `"Loved Mercado da Ribeira, Lisbon — great food court"` tagged with `destination="Lisbon"`

### `build_itinerary(destination: str, days: list[dict]) → None`
Structures the conversation into a day-by-day plan and sends it to the Chainlit custom panel. Each day contains time-slotted entries with type icons: 🍜 food, 🏯 culture/history, 🚶 walking tour, 🌿 nature, 📍 viewpoint.

---

## Memory System

**Static profile** (`interests.json`): loaded on every conversation start. Edited manually or via onboarding flow.

**SQLite memories table:**
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    fact TEXT NOT NULL,
    destination TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Last 20 memories injected into system prompt at conversation start. Future conversations about a destination surface relevant past memories automatically.

---

## Itinerary Panel

Custom Chainlit element rendered alongside chat. Displays:
- Day cards with time slots
- Place names + type icons
- Walking tour badge when a free tour is found
- Updates live as the conversation progresses

Triggered via `build_itinerary` tool call. User can ask "refine day 2" and the panel updates.

---

## Onboarding

First run: Chainlit shows a setup screen to fill in traveler names, interests, and food preferences. Writes `interests.json`. Subsequent launches go straight to chat.

---

## Tech Stack

| Piece | Choice |
|---|---|
| UI | Chainlit |
| AI | Claude API — `claude-sonnet-4-6` |
| Search | Tavily API (free tier: 1000 searches/month) |
| Database | SQLite |
| Package management | uv |
| Runtime | Python 3.11+ |

---

## Environment Variables

```
ANTHROPIC_API_KEY=...
TAVILY_API_KEY=...
```

Stored in `.env`, never committed.

---

## Running

```bash
uv run chainlit run app.py
```

---

## Out of Scope

- Booking integrations (flights, hotels)
- Multi-user accounts
- Mobile app
- Deployment / hosting (runs locally)
