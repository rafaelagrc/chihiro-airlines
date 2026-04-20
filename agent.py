# agent.py
import os
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
