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
