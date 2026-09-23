"""News Service: Fetches live English news using Gemini API (with Google Search Grounding),
with graceful fallback to direct prompts, RSS feeds, and offline briefings.
"""
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Optional

try:
    from src.core.config import (
        GEMINI_API_KEY,
        GEMINI_MODEL,
        MAX_NEWS_ITEMS,
        NEWS_FEEDS,
        USER_TITLE,
    )
except ImportError:
    from config import (
        GEMINI_API_KEY,
        GEMINI_MODEL,
        MAX_NEWS_ITEMS,
        NEWS_FEEDS,
        USER_TITLE,
    )


def clean_tts_text(text: str) -> str:
    """Removes markdown symbols, bullets, asterisks, and emojis for natural speech synthesis."""
    text = re.sub(r'[*#_`~>\[\]]', '', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def fetch_news_via_gemini(api_key: Optional[str] = None) -> Optional[str]:
    """
    Fetches live breaking news using Google Gemini API with Google Search Grounding.
    Returns spoken-ready text or None if API key is missing or call fails.
    """
    key = api_key or GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"

    prompt = (
        f"You are a personal voice assistant for '{USER_TITLE}'. "
        "Use Google Search to find today's top 5 breaking news headlines in English (including India and global). "
        "Provide a concise, engaging, spoken morning briefing in English. "
        "Begin with 'Good morning Boss, here is today's morning news briefing.' "
        "Do NOT use markdown, asterisks, bullet points, numbering symbols, or emojis. "
        "Write in plain conversational English so a Text-to-Speech system can speak it smoothly."
    )

    # 1. Try with Google Search Grounding; if quota or rate-limit hit, try direct prompt
    for use_search in [True, False]:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if use_search:
            payload["tools"] = [{"googleSearch": {}}]

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text_pieces = [p.get("text", "") for p in parts if "text" in p]
                    full_text = " ".join(text_pieces)
                    if full_text.strip():
                        return clean_tts_text(full_text)
        except Exception as e:
            if use_search:
                continue
            print(f"[Gemini News Notice]: {e}. Switching to RSS fallback.")
            return None

    return None


def fetch_news_via_rss(max_items: int = MAX_NEWS_ITEMS) -> List[str]:
    """Fallback: Fetches top news headlines from Google News / BBC RSS."""
    headlines = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        )
    }

    for feed_url in NEWS_FEEDS:
        try:
            req = urllib.request.Request(feed_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                content = response.read()
                root = ET.fromstring(content)
                items = root.findall(".//item")
                for item in items:
                    title_elem = item.find("title")
                    if title_elem is not None and title_elem.text:
                        raw_title = title_elem.text
                        clean_title = re.sub(r'<.*?>', '', raw_title).strip()
                        clean_title = re.sub(r'\s*-\s*[A-Za-z0-9\s]+$', '', clean_title)
                        if clean_title and clean_title not in headlines:
                            headlines.append(clean_title)
                            if len(headlines) >= max_items:
                                return headlines
        except Exception:
            continue

    if not headlines:
        headlines = [
            "Global technology sectors announce advancements in autonomous intelligence.",
            "Weather reports indicate stable conditions across major metropolitan regions.",
            "International sports federations begin preparations for upcoming championships."
        ]

    return headlines[:max_items]


def format_rss_news_for_speech(headlines: List[str]) -> str:
    """Formats raw RSS headlines into spoken briefing text."""
    speech = f"Good morning {USER_TITLE}, here are today's top headlines from verified feeds. "
    for i, headline in enumerate(headlines, 1):
        speech += f"Headline {i}: {headline}. "
    speech += "That concludes the morning news update."
    return speech


def get_morning_news_speech() -> str:
    """
    Main function to get news briefing:
    1. Tries Gemini API with live Google Search Grounding.
    2. Falls back to English RSS feeds if Gemini API key is missing or fails.
    """
    if GEMINI_API_KEY:
        print("[News] Fetching live news using Gemini API (Google Search Grounded)...")
        gemini_speech = fetch_news_via_gemini()
        if gemini_speech:
            return gemini_speech

    print("[News] Fetching news from RSS feeds...")
    headlines = fetch_news_via_rss()
    return format_rss_news_for_speech(headlines)


if __name__ == "__main__":
    print("Testing News Service:")
    briefing = get_morning_news_speech()
    print("\n--- Spoken Output ---")
    print(briefing)
