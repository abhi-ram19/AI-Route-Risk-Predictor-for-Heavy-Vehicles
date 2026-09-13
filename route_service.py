"""
Route Service — Module 1
Fetches a driving route between two coordinates using the free public
OSRM demo server (no API key required).

To switch to OpenRouteService later (per original PRD spec), replace
the request in `get_route()` with an ORS call — the return shape
below is what the rest of the app expects, so keep it consistent.
"""

import requests

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"


def get_route(origin: dict, destination: dict):
    """
    Args:
        origin: {"lat": float, "lon": float}
        destination: {"lat": float, "lon": float}

    Returns:
        dict with:
            distance_km: float
            duration_min: float
            geometry: list of [lat, lon] points (for map plotting)
            segments: list of dicts, each ~10km chunk of the route
                      with its own [lat, lon] points (for heatmap module)
        or None if the route could not be fetched.
    """
    coords = f"{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
    url = f"{OSRM_BASE_URL}/{coords}"
    params = {"overview": "full", "geometries": "geojson", "steps": "false"}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        raise RuntimeError(f"Route service error: {e}")

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    route = data["routes"][0]
    distance_km = route["distance"] / 1000.0
    duration_min = route["duration"] / 60.0

    # GeoJSON coords are [lon, lat] — flip to [lat, lon] for folium/plotly
    raw_points = route["geometry"]["coordinates"]
    geometry = [[pt[1], pt[0]] for pt in raw_points]

    segments = _split_into_segments(geometry, distance_km, segment_km=10)

    return {
        "distance_km": round(distance_km, 1),
        "duration_min": round(duration_min, 1),
        "geometry": geometry,
        "segments": segments,
    }


def _split_into_segments(geometry, total_distance_km, segment_km=10):
    """
    Splits the route polyline into ~segment_km chunks for Module 4 (heatmap).
    Uses point-count proportion as a simple approximation (no per-point
    distance accumulation needed for MVP purposes).
    """
    if not geometry or total_distance_km <= 0:
        return []

    num_segments = max(1, round(total_distance_km / segment_km))
    points_per_segment = max(1, len(geometry) // num_segments)

    segments = []
    for i in range(0, len(geometry), points_per_segment):
        chunk = geometry[i:i + points_per_segment]
        if not chunk:
            continue
        segments.append({
            "index": len(segments) + 1,
            "start_km": round(i / max(1, len(geometry) - 1) * total_distance_km, 1),
            "points": chunk,
            "midpoint": chunk[len(chunk) // 2],
        })
    return segments
