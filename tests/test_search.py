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
    with patch("tools.search.TavilyClient", return_value=mock_client), \
         patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
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
    with patch("tools.search.TavilyClient", return_value=mock_client), \
         patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
        result = web_search("test query")
    assert "Result 1" in result
    assert "Result 2" in result

def test_web_search_handles_empty_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}
    with patch("tools.search.TavilyClient", return_value=mock_client), \
         patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
        result = web_search("obscure query")
    assert isinstance(result, str)
    assert result == "No results found."
