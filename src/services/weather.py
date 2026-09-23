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

# In-memory cache to prevent redundant network requests (valid for 10 minutes)
_WEATHER_CACHE = {
    "timestamp": 0,
    "location": "",
    "data": None
}


def _clean_text(text: str) -> str:
    """Removes extra whitespace and cleans weather condition strings."""
    return re.sub(r'\s+', ' ', str(text)).strip()


def fetch_weather_wttr(city: Optional[str] = None) -> Optional[Dict]:
    """Fetches weather data from wttr.in JSON endpoint."""
    target = urllib.parse.quote(city) if city else ""
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


def get_current_weather(city: Optional[str] = None) -> Dict:
    """
    Main function to get today's weather:
    Checks cache first, then tries wttr.in, then Open-Meteo fallback.
    Returns dictionary with metrics and ready-to-speak text.
    """
    global _WEATHER_CACHE
    now = time.time()
    cache_key = (city or "").strip().lower()

    if _WEATHER_CACHE["data"] and _WEATHER_CACHE["location"] == cache_key:
        if now - _WEATHER_CACHE["timestamp"] < 600:  # 10 minute cache
            return _WEATHER_CACHE["data"]

    # 1. Try wttr.in (auto IP geolocation or named city)
    data = fetch_weather_wttr(city)

    # 2. Try Open-Meteo fallback
    if not data:
        data = fetch_weather_openmeteo(city_name=city or "Kolkata")

    # 3. Offline default fallback if internet is completely down
    if not data:
        data = {
            "location": city or "Kolkata",
            "country": "India",
            "temp_c": "26",
            "feels_like_c": "27",
            "condition": "Partly cloudy",
            "humidity": "75",
            "wind_kmph": "10",
            "source": "Offline Fallback"
        }

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
