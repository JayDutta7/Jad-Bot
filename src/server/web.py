"""Web Server: Local zero-dependency, security-hardened HTTP server providing REST API
and serving the animated AI Bot Agent UI/UX on http://localhost:8000.
"""
import json
import os
import urllib.parse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

try:
    from src.core.config import ALARM_FILE, ALARM_HOUR, ALARM_MINUTE, BASE_DIR, TIMEZONE, USER_TITLE
    from src.platform_util.desktop import get_platform_name
    from src.services.news import fetch_news_via_rss, get_conversational_chat_reply, get_morning_news_speech
    from src.services.weather import get_current_weather
except ImportError:
    from config import ALARM_FILE, ALARM_HOUR, ALARM_MINUTE, BASE_DIR, TIMEZONE, USER_TITLE
    from desktop_helper import get_platform_name
    from news_service import fetch_news_via_rss, get_conversational_chat_reply, get_morning_news_speech
    from services.weather import get_current_weather

UI_DIR = os.path.join(BASE_DIR, "ui")
MAX_REQUEST_BODY_SIZE = 65536  # 64 KB max payload to prevent Denial of Service


class BotAPIServer:
    """Manages bot instance reference and shared state for the Web API."""
    bot_instance = None
    agent_state = "idle"  # idle, ringing, listening, thinking, speaking
    last_spoken_message = f"Hello {USER_TITLE}, how may I help you?"
    transcript = [
        {"sender": "bot", "text": f"Hello {USER_TITLE}, how may I help you?"}
    ]


class BotRequestHandler(SimpleHTTPRequestHandler):
    """Handles static UI file delivery and REST API requests with security controls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def log_message(self, format, *args):
        """Suppress standard HTTP request logging for a cleaner terminal."""
        pass

    def _is_allowed_origin(self) -> bool:
        """Security Check: Verify request origin is strictly localhost or 127.0.0.1."""
        origin = self.headers.get("Origin", "")
        if not origin:
            return True  # Direct same-origin request
        parsed = urllib.parse.urlparse(origin)
        return parsed.hostname in ("localhost", "127.0.0.1")

    def _send_json_response(self, data: dict, status: int = 200):
        """Helper to send a secure JSON response with strict CORS headers."""
        encoded = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")

        # Strict CORS: Only reflect allowed localhost origin
        if self._is_allowed_origin():
            origin = self.headers.get("Origin") or "http://localhost:8000"
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests safely."""
        if not self._is_allowed_origin():
            self.send_error(HTTPStatus.FORBIDDEN, "Cross-origin request forbidden")
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        origin = self.headers.get("Origin") or "http://localhost:8000"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        # Security: Block cross-origin GET requests from external malicious sites
        if not self._is_allowed_origin():
            self.send_error(HTTPStatus.FORBIDDEN, "Cross-origin request forbidden")
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self._handle_status()
            return
        elif path == "/api/news":
            self._handle_get_news()
            return
        elif path == "/api/weather":
            self._handle_get_weather()
            return
        elif path == "/alarm_sound.wav":
            if os.path.exists(ALARM_FILE):
                with open(ALARM_FILE, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(content)
                return

        # Serve static UI files
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        # Security: Prevent CSRF from unauthorized external origins
        if not self._is_allowed_origin():
            self.send_error(HTTPStatus.FORBIDDEN, "Cross-origin request forbidden")
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Security: Limit request body to prevent Denial of Service (DoS) memory exhaustion
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > MAX_REQUEST_BODY_SIZE:
            self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Payload exceeds 64KB limit")
            return

        body = {}
        if content_length > 0:
            try:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                body = json.loads(raw_body)
            except Exception:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON payload")
                return

        if path == "/api/test-alarm":
            self._handle_test_alarm()
        elif path == "/api/stop-alarm":
            self._handle_stop_alarm()
        elif path == "/api/trigger-routine":
            self._handle_trigger_routine()
        elif path == "/api/welcome":
            self._handle_welcome()
        elif path == "/api/chat":
            self._handle_chat(body)
        elif path == "/api/speak":
            self._handle_speak(body)
        elif path == "/api/toggle-sleep":
            self._handle_toggle_sleep()
        else:
            self._send_json_response({"error": "Endpoint not found"}, status=404)

    def _handle_status(self):
        bot = BotAPIServer.bot_instance
        if bot:
            now = bot.get_current_time()
            secs, target = bot.get_seconds_until_next_alarm()
            is_ringing = bot.alarm.is_ringing
            sleep_active = bot.sleep_preventer._is_active
        else:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo(TIMEZONE))
            secs = 0
            target = now
            is_ringing = False
            sleep_active = False

        if is_ringing:
            BotAPIServer.agent_state = "ringing"
        elif BotAPIServer.agent_state == "ringing" and not is_ringing:
            BotAPIServer.agent_state = "idle"

        data = {
            "platform": get_platform_name(),
            "timezone": TIMEZONE,
            "user_title": USER_TITLE,
            "alarm_hour": ALARM_HOUR,
            "alarm_minute": ALARM_MINUTE,
            "current_time_str": now.strftime("%Y-%m-%d %I:%M:%S %p"),
            "current_time_iso": now.isoformat(),
            "next_alarm_iso": target.isoformat(),
            "next_alarm_str": target.strftime("%Y-%m-%d %I:%M:%S %p"),
            "seconds_remaining": max(0, int(secs)),
            "is_ringing": is_ringing,
            "sleep_prevention_active": sleep_active,
            "agent_state": BotAPIServer.agent_state,
            "last_spoken": BotAPIServer.last_spoken_message,
            "transcript": BotAPIServer.transcript[-20:]
        }
        self._send_json_response(data)

    def _handle_test_alarm(self):
        bot = BotAPIServer.bot_instance
        if bot:
            import threading
            import time
            def _ring_5s():
                BotAPIServer.agent_state = "ringing"
                bot.alarm.start_ringing()
                time.sleep(5)
                bot.alarm.stop_ringing()
                BotAPIServer.agent_state = "idle"
            threading.Thread(target=_ring_5s, daemon=True).start()
            self._send_json_response({"status": "Alarm test started for 5 seconds"})
        else:
            self._send_json_response({"error": "Bot instance not initialized"}, status=500)

    def _handle_stop_alarm(self):
        bot = BotAPIServer.bot_instance
        if bot:
            bot.alarm.stop_ringing()
            BotAPIServer.agent_state = "idle"
            BotAPIServer.transcript.append({"sender": "user", "text": "Dismiss Alarm"})
            BotAPIServer.transcript.append({"sender": "bot", "text": f"Alarm silenced. Good morning {USER_TITLE}!"})
            self._send_json_response({"status": "Alarm silenced"})
        else:
            self._send_json_response({"error": "Bot instance not initialized"}, status=500)

    def _handle_trigger_routine(self):
        bot = BotAPIServer.bot_instance
        if bot:
            import threading
            threading.Thread(target=bot.trigger_morning_routine, daemon=True).start()
            self._send_json_response({"status": "Routine triggered"})
        else:
            self._send_json_response({"error": "Bot instance not initialized"}, status=500)

    def _handle_get_news(self):
        headlines = fetch_news_via_rss(max_items=6)
        self._send_json_response({"headlines": headlines})

    def _handle_get_weather(self):
        weather_data = get_current_weather()
        self._send_json_response(weather_data)

    def _handle_welcome(self):
        bot = BotAPIServer.bot_instance
        welcome_text = f"Hello {USER_TITLE}, how may I help you?"
        BotAPIServer.last_spoken_message = welcome_text
        if bot:
            import threading
            threading.Thread(target=bot.speak_welcome_greeting, daemon=True).start()
        self._send_json_response({"message": welcome_text})

    def _handle_chat(self, body: dict):
        bot = BotAPIServer.bot_instance
        user_msg = str(body.get("message", "")).strip()[:1000]
        if not user_msg:
            self._send_json_response({"error": "Empty message"}, status=400)
            return

        BotAPIServer.transcript.append({"sender": "user", "text": user_msg})
        cleaned = user_msg.lower()

        if bot and bot.alarm.is_ringing:
            bot.alarm.stop_ringing()
            reply = f"Good morning {USER_TITLE}! Alarm silenced. How can I help you today?"
            BotAPIServer.agent_state = "speaking"
        elif any(w in cleaned for w in ["good morning", "morning"]):
            reply = f"Good morning {USER_TITLE}! Wishing you an energizing and productive day ahead!"
        elif any(w in cleaned for w in ["news", "headline", "headlines", "latest"]):
            reply = get_morning_news_speech()
        elif any(w in cleaned for w in ["weather", "temperature", "forecast", "climate", "rain", "umbrella", "how is the weather", "what is the weather"]):
            weather_data = get_current_weather()
            reply = weather_data.get("spoken_text", f"The weather report is currently being updated for {USER_TITLE}.")
        elif any(w in cleaned for w in ["that's all", "that is all", "stop", "exit", "bye", "thanks", "thank you"]):
            reply = f"Have an outstanding day ahead, {USER_TITLE}! I will stand by for tomorrow's 6:00 AM wake up."
        else:
            reply = get_conversational_chat_reply(user_msg)

        BotAPIServer.last_spoken_message = reply
        BotAPIServer.transcript.append({"sender": "bot", "text": reply})

        if bot:
            import threading
            def _async_speak():
                BotAPIServer.agent_state = "speaking"
                bot.voice.speak(reply)
                BotAPIServer.agent_state = "idle"
            threading.Thread(target=_async_speak, daemon=True).start()

        self._send_json_response({"reply": reply, "agent_state": "speaking"})

    def _handle_speak(self, body: dict):
        bot = BotAPIServer.bot_instance
        text = str(body.get("text", "")).strip()[:1000]
        if bot and text:
            import threading
            def _async_speak():
                BotAPIServer.agent_state = "speaking"
                bot.voice.speak(text)
                BotAPIServer.agent_state = "idle"
            threading.Thread(target=_async_speak, daemon=True).start()
        self._send_json_response({"status": "Speaking text"})

    def _handle_toggle_sleep(self):
        bot = BotAPIServer.bot_instance
        if bot:
            preventer = bot.sleep_preventer
            if preventer._is_active:
                preventer.deactivate()
                state = False
            else:
                preventer.activate()
                state = True
            self._send_json_response({"sleep_prevention_active": state})
        else:
            self._send_json_response({"error": "Bot instance not initialized"}, status=500)


def start_web_server(bot=None, port: int = 8000, open_browser: bool = True):
    """Starts the ThreadingHTTPServer on the specified port bound strictly to localhost."""
    import webbrowser
    BotAPIServer.bot_instance = bot
    server_address = ("127.0.0.1", port)

    try:
        httpd = ThreadingHTTPServer(server_address, BotRequestHandler)
    except OSError:
        port = 8080
        server_address = ("127.0.0.1", port)
        httpd = ThreadingHTTPServer(server_address, BotRequestHandler)

    url = f"http://localhost:{port}"
    print(f"\n✨ [Animated AI Agent UI] Online at {url}")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    return httpd


if __name__ == "__main__":
    from src.core.bot import WakeUpBot
    bot = WakeUpBot()
    server = start_web_server(bot, port=8000, open_browser=True)
    print("Serving AI Bot Agent UI. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server.")
        server.server_close()
