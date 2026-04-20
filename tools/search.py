# tools/search.py
import os
from tavily import TavilyClient

def web_search(query: str) -> str:
    api_key = os.environ.get("TAVILY_API_KEY", "")
    client = TavilyClient(api_key=api_key)
    response = client.search(query, max_results=5)
    results = response.get("results", [])
    if not results:
        return "No results found."
    parts = []
    for r in results:
        parts.append(f"**{r['title']}**\n{r['content']}")
    return "\n\n".join(parts)
