"""
Risk Engine — Module 3
Combines weather, traffic, visibility, duration, road type, and time-of-day
into a single 0-100 Route Risk Score, using the weights specified in the PRD:

    Rain              25%
    Traffic           30%
    Visibility        15%
    Travel Duration   10%
    Road Type         10%
    Time of Day       10%

NOTE ON DATA HONESTY:
Rain, humidity, wind, and visibility come from real weather data.
Traffic and road-type risk are HEURISTIC ESTIMATES for this MVP —
there is no free, no-key live traffic API with adequate coverage.
They're modeled from time-of-day patterns and route length as a
reasonable stand-in, clearly labeled as such in the UI. Swap in a
real traffic API (e.g. TomTom, HERE) later for production use.
"""

from datetime import datetime

WEIGHTS = {
    "rain": 0.25,
    "traffic": 0.30,
    "visibility": 0.15,
    "duration": 0.10,
    "road_type": 0.10,
    "time_of_day": 0.10,
}


def _rain_risk(rain_probability_pct):
    """0-100 risk from rain probability."""
    return min(100, rain_probability_pct)


def _visibility_risk(visibility_km):
    """Lower visibility -> higher risk. Assume 10km+ is clear."""
    if visibility_km >= 10:
        return 5
    return min(100, (10 - visibility_km) / 10 * 100)


def _duration_risk(duration_min):
    """Longer trips carry more cumulative risk (fatigue, exposure)."""
    hours = duration_min / 60.0
    if hours <= 2:
        return 15
    if hours <= 5:
        return 35
    if hours <= 8:
        return 60
    return 85


def _road_type_risk(distance_km, duration_min):
    """
    Heuristic road-type proxy: average speed implies highway vs. urban/rural roads.
    Higher average speed -> likely highway (generally safer, well-maintained).
    Lower average speed -> likely urban/rural roads (more intersections, risk).
    """
    if duration_min <= 0:
        return 50
    avg_speed_kmh = distance_km / (duration_min / 60.0)
    if avg_speed_kmh >= 70:
        return 20   # mostly highway
    if avg_speed_kmh >= 45:
        return 45   # mixed roads
    return 70       # slow urban/rural roads


def _time_of_day_risk(departure_hour):
    """Night driving (10PM-5AM) and dawn/dusk glare hours carry more risk."""
    if 22 <= departure_hour or departure_hour < 5:
        return 80   # late night
    if 5 <= departure_hour < 7 or 17 <= departure_hour < 19:
        return 50   # dawn/dusk glare, rush hour
    if 7 <= departure_hour < 10 or 16 <= departure_hour < 17:
        return 40   # rush hour
    return 20        # daytime, off-peak


def _traffic_risk(departure_hour, distance_km):
    """
    Heuristic traffic estimate from time-of-day rush-hour patterns,
    scaled slightly by distance (longer routes cross more traffic zones).
    """
    if 7 <= departure_hour < 10 or 17 <= departure_hour < 20:
        base = 75  # rush hour
    elif 10 <= departure_hour < 17:
        base = 45  # daytime moderate
    elif 20 <= departure_hour < 22:
        base = 35
    else:
        base = 20  # late night / early morning, light traffic

    distance_factor = min(15, distance_km / 50)
    return min(100, base + distance_factor)


def calculate_risk(route: dict, weather: dict, departure_hour: int):
    """
    Args:
        route: output of route_service.get_route()
        weather: output of weather_service.get_weather()
        departure_hour: int, 0-23, planned departure hour

    Returns:
        dict with:
            overall_score: float (0-100)
            factor_scores: dict of each factor's raw 0-100 score
            factor_contributions: dict of each factor's weighted contribution
            risk_level: "Low" | "Medium" | "High"
    """
    rain = _rain_risk(weather["rain_probability_pct"] or 0)
    visibility = _visibility_risk(weather["visibility_km"])
    duration = _duration_risk(route["duration_min"])
    road_type = _road_type_risk(route["distance_km"], route["duration_min"])
    time_of_day = _time_of_day_risk(departure_hour)
    traffic = _traffic_risk(departure_hour, route["distance_km"])

    factor_scores = {
        "rain": rain,
        "traffic": traffic,
        "visibility": visibility,
        "duration": duration,
        "road_type": road_type,
        "time_of_day": time_of_day,
    }

    factor_contributions = {
        k: round(v * WEIGHTS[k], 2) for k, v in factor_scores.items()
    }

    overall_score = round(sum(factor_contributions.values()), 1)
    overall_score = max(0, min(100, overall_score))

    if overall_score < 35:
        risk_level = "Low"
    elif overall_score < 65:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "overall_score": overall_score,
        "factor_scores": factor_scores,
        "factor_contributions": factor_contributions,
        "risk_level": risk_level,
    }


def score_segments(segments, base_weather_risk, departure_hour, distance_km):
    """
    Module 4 — Route Heatmap.
    Assigns each ~10km segment a risk score + color band.
    Adds mild pseudo-random variation per segment (seeded by segment index
    for reproducibility) on top of the base weather/time risk, to simulate
    localized conditions (since hyper-local per-segment weather/traffic
    data isn't available from free APIs for the whole route).
    """
    import random

    scored = []
    for seg in segments:
        rnd = random.Random(seg["index"] * 97 + int(distance_km))
        variation = rnd.uniform(-12, 18)
        score = max(0, min(100, base_weather_risk + variation))

        if score < 35:
            color = "green"
        elif score < 65:
            color = "yellow"
        else:
            color = "red"

        scored.append({
            **seg,
            "risk_score": round(score, 1),
            "color": color,
        })
    return scored
