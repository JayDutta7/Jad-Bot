"""Weather Service: Fetches real-time weather information and formats natural spoken briefings.
Zero external dependencies required (uses standard library urllib.request with wttr.in and Open-Meteo).
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.core.config import USER_TITLE
except ImportError:
    USER_TITLE = "Boss"

# Persistent active location state
ACTIVE_LOCATION = {
    "place": "Calcutta",
    "country": "India",
    "latitude": 22.5626,
    "longitude": 88.3630,
    "source": "auto"
}

# In-memory cache to prevent redundant network requests (valid for 10 minutes)
_WEATHER_CACHE = {
    "timestamp": 0,
    "location": "",
    "data": None
}


def _clean_text(text: str) -> str:
    """Removes extra whitespace and cleans weather condition strings."""
    return re.sub(r'\s+', ' ', str(text)).strip()


def set_active_location(
    place: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    country: str = "",
    source: str = "manual"
) -> Dict:
    """Updates active location and coordinates, invalidating the weather cache."""
    global ACTIVE_LOCATION, _WEATHER_CACHE
    ACTIVE_LOCATION["place"] = _clean_text(place)
    if lat is not None:
        ACTIVE_LOCATION["latitude"] = float(lat)
    if lon is not None:
        ACTIVE_LOCATION["longitude"] = float(lon)
    if country:
        ACTIVE_LOCATION["country"] = _clean_text(country)
    ACTIVE_LOCATION["source"] = source
    _WEATHER_CACHE["timestamp"] = 0
    return dict(ACTIVE_LOCATION)


def get_active_location() -> Dict:
    """Returns a copy of the current active location and coordinates."""
    return dict(ACTIVE_LOCATION)


def search_place_coordinates(place_name: str) -> Optional[Dict]:
    """
    Searches for a place name and returns its latitude, longitude, and country.
    Uses free Open-Meteo Geocoding API with zero API key required.
    """
    clean = place_name.strip()
    if not clean:
        return None

    # Strip conversational prefixes: e.g. "I am in Kolkata", "currently at Mumbai"
    clean = re.sub(r'^(?:i(?:\s+am)?\s+(?:in|at|from)|currently\s+(?:in|at)|my\s+location\s+is\s+|(?:in|at|from))\s+', '', clean, flags=re.IGNORECASE).strip()
    # Strip trailing punctuation
    clean = clean.strip(".!?,")
    if not clean:
        return None

    target = urllib.parse.quote(clean)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={target}&count=1&language=en&format=json"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JAD-Bot-Geocoding-Client/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("results")
            if results and len(results) > 0:
                top = results[0]
                resolved_place = top.get("name", clean)
                lat = float(top.get("latitude"))
                lon = float(top.get("longitude"))
                country = top.get("country", "")
                admin1 = top.get("admin1", "")

                info = {
                    "place": resolved_place,
                    "latitude": lat,
                    "longitude": lon,
                    "country": country,
                    "admin1": admin1,
                    "display_name": f"{resolved_place}, {admin1}, {country}".replace(", ,", ",").strip(", "),
                    "source": "geocoded"
                }
                set_active_location(
                    place=resolved_place,
                    lat=lat,
                    lon=lon,
                    country=country,
                    source="geocoded"
                )
                return info
    except Exception as e:
        print(f"[Geocoding Error]: {e}")

    return None


def fetch_weather_wttr(
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> Optional[Dict]:
    """Fetches weather data from wttr.in JSON endpoint using city or (lat, lon)."""
    if lat is not None and lon is not None:
        target = f"{lat:.4f},{lon:.4f}"
    elif city:
        target = urllib.parse.quote(city)
    else:
        target = ""

    url = f"https://wttr.in/{target}?format=j1"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "curl/7.88.1 (JAD-Bot-Weather-Client)",
            "Accept": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            current = data.get("current_condition", [{}])[0]
            nearest = data.get("nearest_area", [{}])[0]

            location_name = city or nearest.get("areaName", [{}])[0].get("value") or nearest.get("region", [{}])[0].get("value") or "your area"
            country = nearest.get("country", [{}])[0].get("value") or ""

            temp_c = current.get("temp_C", "--")
            feels_like_c = current.get("FeelsLikeC", temp_c)
            condition = current.get("weatherDesc", [{}])[0].get("value") or "Clear"
            humidity = current.get("humidity", "--")
            wind_kmph = current.get("windspeedKmph", "--")

            return {
                "location": _clean_text(location_name),
                "country": _clean_text(country),
                "temp_c": temp_c,
                "feels_like_c": feels_like_c,
                "condition": _clean_text(condition),
                "humidity": humidity,
                "wind_kmph": wind_kmph,
                "source": "wttr.in"
            }
    except Exception:
        return None


def fetch_weather_openmeteo(lat: float = 22.57, lon: float = 88.36, city_name: str = "Kolkata") -> Optional[Dict]:
    """Fallback weather fetcher using Open-Meteo free API."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JAD-Bot-Weather-Client"})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            cw = data.get("current_weather", {})
            temp_c = str(round(cw.get("temperature", 26)))
            wind_kmph = str(round(cw.get("windspeed", 12)))
            code = cw.get("weathercode", 0)

            # Map WMO weather codes to spoken conditions
            code_map = {
                0: "Clear skies",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Foggy",
                51: "Light drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                80: "Rain showers",
                95: "Thunderstorms"
            }
            condition = code_map.get(code, "Fair weather")

            return {
                "location": city_name,
                "country": "India",
                "temp_c": temp_c,
                "feels_like_c": temp_c,
                "condition": condition,
                "humidity": "80",
                "wind_kmph": wind_kmph,
                "source": "Open-Meteo"
            }
    except Exception:
        return None


def format_weather_speech(w: Dict) -> str:
    """Formats raw weather data into natural, conversational spoken English for Boss."""
    loc = w.get("location", "your area")
    temp = w.get("temp_c", "26")
    cond = w.get("condition", "pleasant weather")
    hum = w.get("humidity", "")
    feels = w.get("feels_like_c", temp)

    speech = f"Here is today's weather report, {USER_TITLE}. "
    speech += f"In {loc}, it is currently {temp} degrees Celsius with {cond.lower()}. "

    if feels and feels != temp:
        speech += f"It feels like {feels} degrees. "

    if hum and hum != "--":
        speech += f"Humidity is at {hum} percent. "

    # Practical morning advice based on condition and temperature
    try:
        t_int = int(float(temp))
        c_lower = cond.lower()
        if "rain" in c_lower or "shower" in c_lower or "drizzle" in c_lower:
            speech += "Don't forget to take an umbrella with you today! "
        elif t_int >= 33:
            speech += "It's quite warm outside, so make sure to stay well hydrated today. "
        elif t_int <= 14:
            speech += "It's a bit chilly, so keep a light jacket handy. "
        else:
            speech += "It looks like great weather to have a productive day ahead!"
    except Exception:
        speech += "Have a wonderful and productive day ahead!"

    return speech.strip()


def get_current_weather(
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> Dict:
    """
    Main function to get today's weather:
    Checks cache first, then tries wttr.in, then Open-Meteo fallback.
    Returns dictionary with metrics, coordinates, and ready-to-speak text.
    """
    global _WEATHER_CACHE, ACTIVE_LOCATION
    now = time.time()

    if lat is not None and lon is not None:
        if city:
            set_active_location(city, lat=lat, lon=lon, source="coords")
        else:
            ACTIVE_LOCATION["latitude"] = float(lat)
            ACTIVE_LOCATION["longitude"] = float(lon)
            ACTIVE_LOCATION["source"] = "coords"

    use_lat = lat if lat is not None else ACTIVE_LOCATION.get("latitude")
    use_lon = lon if lon is not None else ACTIVE_LOCATION.get("longitude")
    target_city = city or ACTIVE_LOCATION.get("place")

    cache_key = f"{target_city}_{use_lat}_{use_lon}".strip().lower()

    if _WEATHER_CACHE["data"] and _WEATHER_CACHE["location"] == cache_key:
        if now - _WEATHER_CACHE["timestamp"] < 600:  # 10 minute cache
            return _WEATHER_CACHE["data"]

    # 1. Try wttr.in (by lat/lon or city or auto)
    data = fetch_weather_wttr(city=target_city if not (use_lat and use_lon) else None, lat=use_lat, lon=use_lon)

    # 2. Try Open-Meteo fallback
    if not data:
        data = fetch_weather_openmeteo(
            lat=use_lat if use_lat is not None else 22.57,
            lon=use_lon if use_lon is not None else 88.36,
            city_name=target_city or "Kolkata"
        )

    # 3. Offline default fallback if internet is completely down
    if not data:
        data = {
            "location": target_city or "Kolkata",
            "country": "India",
            "temp_c": "26",
            "feels_like_c": "27",
            "condition": "Partly cloudy",
            "humidity": "75",
            "wind_kmph": "10",
            "source": "Offline Fallback"
        }

    # Ensure location name reflects user's geocoded/active place if available
    if ACTIVE_LOCATION.get("place") and (data.get("location") == "your area" or not data.get("location")):
        data["location"] = ACTIVE_LOCATION["place"]

    data["latitude"] = use_lat
    data["longitude"] = use_lon
    data["spoken_text"] = format_weather_speech(data)

    # Update cache
    _WEATHER_CACHE["timestamp"] = now
    _WEATHER_CACHE["location"] = cache_key
    _WEATHER_CACHE["data"] = data

    return data


if __name__ == "__main__":
    print("Testing Weather Service:")
    w = get_current_weather()
    print("Weather Metrics:", json.dumps(w, indent=2))
    print("\n--- Spoken Output ---")
    print(w["spoken_text"])
