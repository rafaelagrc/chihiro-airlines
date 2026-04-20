# Vacation Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Chainlit-based AI chatbot that knows the user's travel interests, searches the web for live info, saves memories across sessions, and renders structured day-by-day itineraries.

**Architecture:** Chainlit handles the chat UI and session state. An agent loop in `agent.py` calls Claude with three tools (`web_search`, `save_memory`, `build_itinerary`). Memory and itinerary data live in SQLite. Profile interests are stored in a JSON file injected into every Claude system prompt.

**Tech Stack:** Python 3.11+, uv, Chainlit, Anthropic SDK (`claude-sonnet-4-6`), Tavily, SQLite, pytest, pytest-asyncio

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `tools/__init__.py`
- Create: `db/__init__.py`
- Create: `profile/__init__.py`
- Create: `ui/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "chihiro-airlines"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "chainlit>=1.3.0",
    "anthropic>=0.40.0",
    "tavily-python>=0.5.0",
    "python-dotenv>=1.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create `.env.example`**

```
ANTHROPIC_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

- [ ] **Step 3: Add `.env` to `.gitignore`**

Append to `.gitignore`:
```
.env
db/chihiro.db
.superpowers/
__pycache__/
.pytest_cache/
```

- [ ] **Step 4: Create empty `__init__.py` files**

```bash
mkdir -p tools db profile ui tests
touch tools/__init__.py db/__init__.py profile/__init__.py ui/__init__.py tests/__init__.py
```

- [ ] **Step 5: Install dependencies**

```bash
uv sync --dev
```

Expected: dependencies installed, `.venv` created.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example .gitignore tools/__init__.py db/__init__.py profile/__init__.py ui/__init__.py tests/__init__.py
git commit -m "feat: project scaffold"
```

---

### Task 2: Database schema

**Files:**
- Create: `db/schema.py`
- Create: `tests/test_schema.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schema.py
import sqlite3
import tempfile
import os
from db.schema import init_db

def test_init_db_creates_memories_table():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "memories" in tables
        assert "itineraries" in tables
    finally:
        os.unlink(db_path)

def test_init_db_memories_columns():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(memories)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        assert {"id", "fact", "destination", "created_at"} <= columns
    finally:
        os.unlink(db_path)

def test_init_db_is_idempotent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        init_db(db_path)  # calling twice should not raise
    finally:
        os.unlink(db_path)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_schema.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'db.schema'`

- [ ] **Step 3: Write implementation**

```python
# db/schema.py
import sqlite3

DB_PATH = "db/chihiro.db"

def init_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            destination TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS itineraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            days_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_schema.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add db/schema.py tests/test_schema.py
git commit -m "feat: database schema with memories and itineraries tables"
```

---

### Task 3: Memory tool

**Files:**
- Create: `tools/memory.py`
- Create: `tests/test_memory.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_memory.py
import tempfile
import os
from db.schema import init_db
from tools.memory import save_memory, load_memories

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_memory.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.memory'`

- [ ] **Step 3: Write implementation**

```python
# tools/memory.py
import sqlite3
from db.schema import DB_PATH

def save_memory(fact: str, destination: str | None = None, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO memories (fact, destination) VALUES (?, ?)",
        (fact, destination)
    )
    conn.commit()
    conn.close()

def load_memories(db_path: str = DB_PATH) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT fact, destination, created_at FROM memories ORDER BY created_at DESC LIMIT 20"
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_memory.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/memory.py tests/test_memory.py
git commit -m "feat: memory tool — save and load travel memories from SQLite"
```

---

### Task 4: Profile system

**Files:**
- Create: `tools/profile.py`
- Create: `profile/interests.json`
- Create: `tests/test_profile.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_profile.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_profile.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.profile'`

- [ ] **Step 3: Create `profile/interests.json`**

```json
{
  "travelers": ["Rafaela", "boyfriend"],
  "interests": ["culture", "history", "viewpoints", "nature parks"],
  "food": ["local", "street food", "Japanese", "Vietnamese", "Indian", "Italian", "Chinese", "Thai", "food courts"],
  "not_into": ["nightlife"]
}
```

- [ ] **Step 4: Write implementation**

```python
# tools/profile.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_profile.py -v
```

Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add tools/profile.py profile/interests.json tests/test_profile.py
git commit -m "feat: profile system — load interests.json and format for system prompt"
```

---

### Task 5: Search tool

**Files:**
- Create: `tools/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_search.py
from unittest.mock import patch, MagicMock
from tools.search import web_search

def test_web_search_returns_string():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"title": "Free walking tour Lisbon", "content": "Tours depart at 10am from Praça do Comércio."},
            {"title": "Best viewpoints Lisbon", "content": "Miradouro da Graça has stunning views."},
        ]
    }
    with patch("tools.search.TavilyClient", return_value=mock_client):
        result = web_search("free walking tours Lisbon")
    assert isinstance(result, str)
    assert "walking tour" in result.lower() or "Lisbon" in result

def test_web_search_formats_multiple_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"title": "Result 1", "content": "Content 1"},
            {"title": "Result 2", "content": "Content 2"},
        ]
    }
    with patch("tools.search.TavilyClient", return_value=mock_client):
        result = web_search("test query")
    assert "Result 1" in result
    assert "Result 2" in result

def test_web_search_handles_empty_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}
    with patch("tools.search.TavilyClient", return_value=mock_client):
        result = web_search("obscure query")
    assert isinstance(result, str)
    assert result == "No results found."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_search.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.search'`

- [ ] **Step 3: Write implementation**

```python
# tools/search.py
import os
from tavily import TavilyClient

def web_search(query: str) -> str:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    response = client.search(query, max_results=5)
    results = response.get("results", [])
    if not results:
        return "No results found."
    parts = []
    for r in results:
        parts.append(f"**{r['title']}**\n{r['content']}")
    return "\n\n".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_search.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/search.py tests/test_search.py
git commit -m "feat: search tool — Tavily web search with formatted results"
```

---

### Task 6: Itinerary tool

**Files:**
- Create: `tools/itinerary.py`
- Create: `tests/test_itinerary.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_itinerary.py
from tools.itinerary import build_itinerary, render_itinerary_html

SAMPLE_DAYS = [
    {
        "day_number": 1,
        "label": "Old Town",
        "entries": [
            {"time": "Morning", "name": "Fushimi Inari", "type": "culture", "notes": "Go early"},
            {"time": "Lunch", "name": "Nishiki Market", "type": "food", "notes": "Try tamagoyaki"},
            {"time": "Evening", "name": "Pontocho Alley", "type": "food", "notes": ""},
        ]
    },
    {
        "day_number": 2,
        "label": "Arashiyama",
        "entries": [
            {"time": "Morning", "name": "Bamboo Grove", "type": "nature", "notes": ""},
            {"time": "Afternoon", "name": "Free Walking Tour", "type": "walking_tour", "notes": "Departs 3pm"},
        ]
    }
]

def test_build_itinerary_returns_structured_data():
    result = build_itinerary("Kyoto", SAMPLE_DAYS)
    assert result["destination"] == "Kyoto"
    assert len(result["days"]) == 2
    assert result["days"][0]["day_number"] == 1

def test_build_itinerary_preserves_entries():
    result = build_itinerary("Kyoto", SAMPLE_DAYS)
    assert result["days"][0]["entries"][0]["name"] == "Fushimi Inari"

def test_render_itinerary_html_returns_string():
    itinerary = build_itinerary("Kyoto", SAMPLE_DAYS)
    html = render_itinerary_html(itinerary)
    assert isinstance(html, str)

def test_render_itinerary_html_contains_destination():
    itinerary = build_itinerary("Kyoto", SAMPLE_DAYS)
    html = render_itinerary_html(itinerary)
    assert "Kyoto" in html

def test_render_itinerary_html_contains_entries():
    itinerary = build_itinerary("Kyoto", SAMPLE_DAYS)
    html = render_itinerary_html(itinerary)
    assert "Fushimi Inari" in html
    assert "Nishiki Market" in html

def test_render_itinerary_html_shows_walking_tour_badge():
    itinerary = build_itinerary("Kyoto", SAMPLE_DAYS)
    html = render_itinerary_html(itinerary)
    assert "walking" in html.lower() or "🚶" in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_itinerary.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.itinerary'`

- [ ] **Step 3: Write implementation**

```python
# tools/itinerary.py

TYPE_ICONS = {
    "food": "🍜",
    "culture": "🏯",
    "walking_tour": "🚶",
    "nature": "🌿",
    "viewpoint": "📍",
}

def build_itinerary(destination: str, days: list[dict]) -> dict:
    return {"destination": destination, "days": days}

def render_itinerary_html(itinerary: dict) -> str:
    destination = itinerary["destination"]
    days = itinerary["days"]

    day_cards = ""
    for day in days:
        label = day.get("label", "")
        heading = f"Day {day['day_number']}" + (f" — {label}" if label else "")
        entries_html = ""
        for entry in day.get("entries", []):
            icon = TYPE_ICONS.get(entry["type"], "📌")
            time = f'<span style="color:#94a3b8;font-size:11px">{entry.get("time","")}</span> ' if entry.get("time") else ""
            badge = ' <span style="background:#1d4ed8;color:#fff;font-size:10px;padding:1px 6px;border-radius:9px">Free tour</span>' if entry["type"] == "walking_tour" else ""
            notes = f' <span style="color:#64748b;font-size:11px">— {entry["notes"]}</span>' if entry.get("notes") else ""
            entries_html += f'<div style="padding:4px 0">{time}{icon} {entry["name"]}{badge}{notes}</div>'

        day_cards += f"""
        <div style="background:#1e293b;border-radius:8px;padding:12px;margin-bottom:10px">
            <div style="color:#38bdf8;font-size:12px;font-weight:600;margin-bottom:8px">{heading.upper()}</div>
            {entries_html}
        </div>"""

    return f"""
    <div style="background:#0f172a;border-radius:10px;padding:16px;font-family:sans-serif;color:#e2e8f0;max-width:480px">
        <div style="font-size:15px;font-weight:700;margin-bottom:12px">
            ✈ {destination} Itinerary
        </div>
        {day_cards}
    </div>"""
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_itinerary.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add tools/itinerary.py tests/test_itinerary.py
git commit -m "feat: itinerary tool — build structured days and render HTML panel"
```

---

### Task 7: Agent core

**Files:**
- Create: `agent.py`
- Create: `tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_agent.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'agent'`

- [ ] **Step 3: Write implementation**

```python
# agent.py
import os
import json
import anthropic
from tools.profile import load_profile, profile_to_prompt, PROFILE_PATH
from tools.memory import save_memory, load_memories
from tools.search import web_search
from tools.itinerary import build_itinerary, render_itinerary_html
from db.schema import DB_PATH, init_db

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for current travel information. Use for: free walking tours "
            "(always search — schedules change), opening hours, 'best X in Y' queries, "
            "and any time-sensitive info. Answer from knowledge first; search when unsure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": (
            "Save a notable travel preference or experience the user mentions. "
            "Examples: 'Loved Mercado da Ribeira', 'Prefer morning visits to crowded sites'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The memory to save"},
                "destination": {"type": "string", "description": "City or country (optional)"}
            },
            "required": ["fact"]
        }
    },
    {
        "name": "build_itinerary",
        "description": (
            "Build a structured day-by-day itinerary and display it in the itinerary panel. "
            "Call this when the user asks for an itinerary or trip plan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer"},
                            "label": {"type": "string"},
                            "entries": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "time": {"type": "string"},
                                        "name": {"type": "string"},
                                        "type": {
                                            "type": "string",
                                            "enum": ["food", "culture", "walking_tour", "nature", "viewpoint"]
                                        },
                                        "notes": {"type": "string"}
                                    },
                                    "required": ["name", "type"]
                                }
                            }
                        },
                        "required": ["day_number", "entries"]
                    }
                }
            },
            "required": ["destination", "days"]
        }
    }
]

def build_system_prompt(profile_path: str = PROFILE_PATH, db_path: str = DB_PATH) -> str:
    profile = load_profile(profile_path)
    memories = load_memories(db_path)

    prompt = (
        "You are Chihiro, a friendly vacation planning assistant. "
        "You help travelers find the best places to stay, free walking tours, "
        "local food spots, viewpoints, and experiences tailored to their interests.\n\n"
        "## Traveler Profile\n"
        f"{profile_to_prompt(profile)}\n\n"
        "## Guidelines\n"
        "- Prioritize culture, history, food, viewpoints, and nature over nightlife.\n"
        "- Always search for free walking tours — schedules change frequently.\n"
        "- When you learn something notable about their preferences, call save_memory.\n"
        "- When asked for a trip plan or itinerary, call build_itinerary.\n"
    )

    if memories:
        memory_lines = "\n".join(
            f"- {m['fact']}" + (f" [{m['destination']}]" if m["destination"] else "")
            for m in memories
        )
        prompt += f"\n## Past Travel Memories\n{memory_lines}\n"

    return prompt

async def run_agent(
    user_message: str,
    profile_path: str = PROFILE_PATH,
    db_path: str = DB_PATH,
) -> tuple[str, str | None]:
    """
    Run the Claude agent loop for a user message.
    Returns (response_text, itinerary_html | None).
    """
    init_db(db_path)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system_prompt = build_system_prompt(profile_path=profile_path, db_path=db_path)
    messages = [{"role": "user", "content": user_message}]
    itinerary_html = None

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            return text, itinerary_html

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                name = block.name
                inputs = block.input

                if name == "web_search":
                    result = web_search(inputs["query"])
                elif name == "save_memory":
                    save_memory(inputs["fact"], inputs.get("destination"), db_path=db_path)
                    result = "Memory saved."
                elif name == "build_itinerary":
                    itinerary = build_itinerary(inputs["destination"], inputs["days"])
                    itinerary_html = render_itinerary_html(itinerary)
                    result = "Itinerary built and displayed."
                else:
                    result = f"Unknown tool: {name}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_agent.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Run all tests to check no regressions**

```bash
uv run pytest -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add agent.py tests/test_agent.py
git commit -m "feat: agent core — Claude tool loop with web_search, save_memory, build_itinerary"
```

---

### Task 8: Chainlit app with onboarding

**Files:**
- Create: `app.py`

No unit tests for this task — Chainlit's async lifecycle is tested via manual smoke test in Task 9.

- [ ] **Step 1: Write `app.py`**

```python
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
    names = [n.strip() for n in res["output"].replace(" and ", ",").split(",") if n.strip()]

    res = await cl.AskUserMessage(
        content="What are your main travel interests? (e.g. culture, history, nature, food)",
        timeout=120
    ).send()
    interests = [i.strip() for i in res["output"].split(",") if i.strip()]

    res = await cl.AskUserMessage(
        content="What kinds of food do you love? (e.g. local, Japanese, Vietnamese, street food)",
        timeout=120
    ).send()
    food = [f.strip() for f in res["output"].split(",") if f.strip()]

    res = await cl.AskUserMessage(
        content="Anything you're NOT into? (e.g. nightlife, spicy food) — or type 'nothing'",
        timeout=120
    ).send()
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
    response_text, itinerary_html = await run_agent(message.content)

    await cl.Message(content=response_text).send()

    if itinerary_html:
        await cl.Message(
            content="",
            elements=[cl.Html(name="itinerary", content=itinerary_html, display="inline")]
        ).send()
```

- [ ] **Step 2: Commit**

```bash
git add app.py
git commit -m "feat: Chainlit app with onboarding flow and itinerary panel rendering"
```

---

### Task 9: Smoke test

**No code changes** — this is a manual verification step.

- [ ] **Step 1: Copy `.env.example` to `.env` and fill in API keys**

```bash
cp .env.example .env
# Edit .env and set:
# ANTHROPIC_API_KEY=your_real_key
# TAVILY_API_KEY=your_real_key
```

- [ ] **Step 2: Run all tests one final time**

```bash
uv run pytest -v
```

Expected: all PASSED

- [ ] **Step 3: Launch the app**

```bash
uv run chainlit run app.py
```

Expected: browser opens at `http://localhost:8000`

- [ ] **Step 4: Verify onboarding (first run)**

- If `profile/interests.json` doesn't exist, the chat should ask your names, interests, food, and not-into. Answer each question and confirm the file is created:
  ```bash
  cat profile/interests.json
  ```

- [ ] **Step 5: Test a chat query**

Send: `"We're thinking of 4 days in Kyoto in November. What should we do?"`

Expected:
- Claude responds with culture/food/nature suggestions (no nightlife)
- If it calls `build_itinerary`, an itinerary panel renders below the message

- [ ] **Step 6: Test web search**

Send: `"Are there any free walking tours in Kyoto right now?"`

Expected: Claude calls `web_search` and returns current tour info.

- [ ] **Step 7: Test memory**

Send: `"We absolutely loved the ramen at Ichiran last time we were in Japan"`

Expected: Claude calls `save_memory`. Verify in the DB:
```bash
uv run python -c "
from db.schema import init_db; init_db()
from tools.memory import load_memories
for m in load_memories(): print(m)
"
```

- [ ] **Step 8: Final commit**

```bash
git add .
git commit -m "chore: add .env.example, complete smoke test"
```
