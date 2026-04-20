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
