"""Configuration settings for the Wake Up Bot."""
import os

# Root directory of the project
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CORE_DIR)
BASE_DIR = os.path.dirname(SRC_DIR)

def _load_env_file():
    """Lightweight loader for .env file without external dependencies."""
    search_paths = [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(SRC_DIR, ".env"),
    ]
    for env_path in search_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("'\"")
                            if key not in os.environ:
                                os.environ[key] = val
            except Exception:
                pass

_load_env_file()

# Timezone: GMT +5:30 (India Standard Time)
TIMEZONE = "Asia/Kolkata"

# Alarm Target Times (24-hour format)
# Default Mon-Sat: 6:30 AM IST; Sunday: 7:00 AM IST
ALARM_HOUR = 6
ALARM_MINUTE = 30
SUNDAY_ALARM_HOUR = 7
SUNDAY_ALARM_MINUTE = 0

from datetime import datetime
from typing import Optional

# Persona & Response Configuration
USER_TITLE = "Boss"

def get_time_of_day(dt: Optional[datetime] = None) -> str:
    """
    Returns 'morning', 'noon', 'afternoon', or 'evening' based on current local time in TIMEZONE:
    - 05:00 - 11:59: 'morning'
    - 12:00 - 12:59: 'noon'
    - 13:00 - 16:59: 'afternoon'
    - 17:00 - 23:59 & 00:00 - 04:59: 'evening'
    """
    if dt is None:
        try:
            from zoneinfo import ZoneInfo
            dt = datetime.now(ZoneInfo(TIMEZONE))
        except Exception:
            dt = datetime.now()
    hour = dt.hour
    if 5 <= hour < 12:
        return "morning"
    elif hour == 12:
        return "noon"
    elif 13 <= hour < 17:
        return "afternoon"
    else:
        return "evening"


def get_time_of_day_greeting(dt: Optional[datetime] = None) -> str:
    """
    Returns 'Good morning', 'Good noon', 'Good afternoon', or 'Good evening' based on local time.
    """
    tod = get_time_of_day(dt)
    if tod == "morning":
        return "Good morning"
    elif tod == "noon":
        return "Good noon"
    elif tod == "afternoon":
        return "Good afternoon"
    else:
        return "Good evening"


def get_greeting_response(dt: Optional[datetime] = None) -> str:
    """Dynamic greeting reply based on current local time."""
    return f"{get_time_of_day_greeting(dt)} {USER_TITLE}, how can I help you?"


def get_welcome_greeting(dt: Optional[datetime] = None) -> str:
    """Dynamic opening welcome greeting based on current local time."""
    return f"{get_time_of_day_greeting(dt)} {USER_TITLE}, how may I help you?"


GREETING_TRIGGER = "good morning"
GREETING_TRIGGERS = [
    "good morning", "morning",
    "good noon", "noon",
    "good afternoon", "afternoon",
    "good evening", "evening",
    "hello", "hi", "hey"
]
GREETING_RESPONSE = f"Good morning {USER_TITLE}, how can I help you?"
WAKE_WORDS = ["hello jad", "hey jad", "hi jad", "jad", "activate jad"]
WAKE_RESPONSE = f"Hello {USER_TITLE}, I am active and listening. How may I help you?"

# Gemini API Configuration for Real-Time Grounded News Search
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.6-flash"

# Fallback News Configuration (RSS feeds if Gemini API key is missing or offline)
MAX_NEWS_ITEMS = 5
NEWS_FEEDS = [
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "https://feeds.bbci.co.uk/news/world/rss.xml"
]

# Audio / Alarm settings
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ALARM_FILE = os.path.join(ASSETS_DIR, "alarm_sound.wav")
# Fallback to root alarm_sound.wav if assets not found
if not os.path.exists(ALARM_FILE) and os.path.exists(os.path.join(BASE_DIR, "alarm_sound.wav")):
    ALARM_FILE = os.path.join(BASE_DIR, "alarm_sound.wav")

MAX_ALARM_RING_SECONDS = 120  # Auto-timeout if no response after 2 minutes
