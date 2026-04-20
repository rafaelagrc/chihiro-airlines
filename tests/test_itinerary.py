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
