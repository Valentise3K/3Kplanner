from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from timezonefinder import TimezoneFinder

from config import logger

_geolocator = Nominatim(user_agent="planner_bot_v2")
_tf = TimezoneFinder()


async def geocode_city(city: str) -> tuple[float, float] | None:
    """Return (lat, lon) for a city name, or None if not found."""
    try:
        location = _geolocator.geocode(city, timeout=10)
        if location:
            return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.warning("Geocoding error for '%s': %s", city, e)
    return None


async def resolve_timezone(city: str) -> str | None:
    """Return IANA timezone string for a city, or None if unresolvable."""
    coords = await geocode_city(city)
    if coords is None:
        return None
    lat, lon = coords
    tz = _tf.timezone_at(lat=lat, lng=lon)
    return tz
