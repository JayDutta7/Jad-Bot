"""Services and external integrations package."""
from .news import (
    clean_tts_text,
    fetch_news_via_gemini,
    fetch_news_via_rss,
    format_rss_news_for_speech,
    get_conversational_chat_reply,
    get_morning_news_speech,
)
from .weather import get_current_weather

__all__ = [
    "clean_tts_text",
    "fetch_news_via_gemini",
    "fetch_news_via_rss",
    "format_rss_news_for_speech",
    "get_conversational_chat_reply",
    "get_morning_news_speech",
    "get_current_weather",
]
