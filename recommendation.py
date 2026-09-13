"""
Recommendation Engine — Module 5
Turns risk factor scores + weather + segment data into plain-language,
actionable recommendations for the driver/fleet manager.

This is a rules-based engine (not an LLM call) — deterministic, fast,
and free to run, matching the PRD's <5s response requirement.
"""


def generate_recommendations(risk_result: dict, weather: dict, segments: list, departure_hour: int):
    recs = []
    scores = risk_result["factor_scores"]

    # Rain / weather guidance
    if scores["rain"] >= 60:
        recs.append("Heavy rainfall is likely along this route — consider delaying departure or reducing speed on wet sections.")
    elif scores["rain"] >= 30:
        recs.append("Moderate chance of rain expected — keep wipers and headlights ready.")

    # Visibility
    if scores["visibility"] >= 60:
        recs.append("Visibility is poor for parts of the day — avoid this window if possible, or use fog lights and increase following distance.")

    # Traffic / time of day
    if scores["traffic"] >= 70:
        recs.append(f"Heavy traffic expected around the {_format_hour(departure_hour)} departure window — consider shifting departure by 2-3 hours to avoid peak congestion.")
    elif scores["traffic"] >= 45:
        recs.append("Moderate traffic congestion is likely — add a buffer of 15-20 minutes to your ETA.")

    # Time of day (night driving)
    if scores["time_of_day"] >= 70:
        recs.append("Late-night driving carries higher fatigue and reduced-visibility risk — ensure driver is well-rested and consider a relief driver for long hauls.")

    # Duration / fatigue
    if scores["duration"] >= 60:
        recs.append("This is a long trip — schedule rest stops every 2-3 hours to reduce driver fatigue risk.")

    # Road type
    if scores["road_type"] >= 60:
        recs.append("Route includes significant urban/rural roads with more intersections — allow extra time and drive cautiously through populated areas.")

    # Highlight risky segments
    high_risk_segments = [s for s in segments if s.get("color") == "red"]
    if high_risk_segments:
        km_markers = ", ".join(f"Km {s['start_km']}" for s in high_risk_segments[:3])
        recs.append(f"Elevated risk detected near {km_markers} — stay alert through these stretches.")

    # Best departure time suggestion
    best_hour = _suggest_best_departure(departure_hour, scores)
    if best_hour is not None and best_hour != departure_hour:
        recs.append(f"Recommended departure time: around {_format_hour(best_hour)} for lower overall route risk.")

    if not recs:
        recs.append("Conditions look favorable — no major risk factors detected for this route and time.")

    return recs


def _format_hour(hour):
    hour = hour % 24
    period = "AM" if hour < 12 else "PM"
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour}:00 {period}"


def _suggest_best_departure(current_hour, scores):
    """
    Simple heuristic: if traffic or time-of-day risk is high, suggest
    the nearest low-risk window (early morning off-peak, e.g. 6 AM or 9 PM-10PM window).
    """
    if scores["traffic"] >= 70 or scores["time_of_day"] >= 70:
        # Suggest early morning off-peak departure
        return 6
    return None
