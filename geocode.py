"""
Geocoding utility — converts a place name (city, address, landmark)
into (latitude, longitude) using OpenStreetMap's Nominatim service via geopy.

No API key required. Please respect Nominatim's usage policy (max ~1 request/sec).
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

_geolocator = Nominatim(user_agent="ai_route_risk_predictor")


def geocode_place(place_name: str):
    """
    Convert a place name into coordinates.

    Args:
        place_name: e.g. "Visakhapatnam, India" or "Hyderabad"

    Returns:
        dict with keys: lat, lon, address  — or None if not found.
    """
    if not place_name or not place_name.strip():
        return None

    try:
        location = _geolocator.geocode(place_name, timeout=10)
        if location is None:
            return None
        return {
            "lat": location.latitude,
            "lon": location.longitude,
            "address": location.address,
        }
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        raise RuntimeError(f"Geocoding service error: {e}")
