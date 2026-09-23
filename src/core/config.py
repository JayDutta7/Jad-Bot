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

# Alarm Target Time (24-hour format)
ALARM_HOUR = 6
ALARM_MINUTE = 0

# Persona & Response Configuration
USER_TITLE = "Boss"
GREETING_TRIGGER = "good morning"
GREETING_RESPONSE = f"Good morning {USER_TITLE}, how can I help you?"

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
