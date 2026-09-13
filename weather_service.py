"""
Weather Service — Module 2
Fetches current + short-term forecast weather using Open-Meteo
(free, no API key required).

To switch to OpenWeather later (per original PRD spec), replace the
request in `get_weather()` — keep the return shape consistent.
"""

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(lat: float, lon: float):
    """
    Args:
        lat, lon: coordinates to fetch weather for

    Returns:
        dict with:
            temperature_c: float
            rain_probability_pct: float
            humidity_pct: float
            wind_speed_kmh: float
            visibility_km: float (Open-Meteo doesn't give visibility directly;
                                   estimated from cloud cover + precipitation)
            hourly: list of next 12 hours' {time, temp, rain_prob}
        or None if the request failed.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        "hourly": "temperature_2m,precipitation_probability,cloud_cover",
        "forecast_days": 1,
        "timezone": "auto",
    }

    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f"Weather service error: {e}")

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    hourly_list = []
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rain_probs = hourly.get("precipitation_probability", [])
    clouds = hourly.get("cloud_cover", [])

    for i in range(min(12, len(times))):
        hourly_list.append({
            "time": times[i],
            "temp": temps[i] if i < len(temps) else None,
            "rain_prob": rain_probs[i] if i < len(rain_probs) else 0,
            "cloud_cover": clouds[i] if i < len(clouds) else 0,
        })

    # Estimate a rough "visibility" score since Open-Meteo has no direct field:
    # high cloud cover + precipitation = lower visibility.
    current_cloud = clouds[0] if clouds else 0
    current_precip = current.get("precipitation", 0) or 0
    visibility_km = max(1.0, 10.0 - (current_cloud / 100.0 * 6) - (current_precip * 2))

    current_rain_prob = rain_probs[0] if rain_probs else 0

    return {
        "temperature_c": current.get("temperature_2m"),
        "rain_probability_pct": current_rain_prob,
        "humidity_pct": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "visibility_km": round(visibility_km, 1),
        "hourly": hourly_list,
    }
