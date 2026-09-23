"""Main Orchestrator Entrypoint: Daily 6:00 AM GMT+5:30 Wake Up Bot & Morning Assistant.
Supports Desktop (macOS / Windows), Web UI Dashboard, and Mobile (Android).
"""
import argparse
import os
import sys
import threading
import time

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.bot import WakeUpBot
from src.platform_util.desktop import show_desktop_notification
from src.services.news import get_morning_news_speech


def main():
    parser = argparse.ArgumentParser(description="Daily 6:00 AM Wake Up & News Assistant Bot (macOS, Windows, Android)")
    parser.add_argument("--now", action="store_true", help="Trigger the alarm and morning routine right now for testing")
    parser.add_argument("--test-news", action="store_true", help="Fetch and speak the latest English news right now")
    parser.add_argument("--test-alarm", action="store_true", help="Test the device alarm sound for 5 seconds")
    parser.add_argument("--test-notification", action="store_true", help="Test desktop banner/toast notification")
    parser.add_argument("--status", action="store_true", help="Show current time in GMT+5:30 and countdown to next alarm")
    parser.add_argument("--no-sleep-lock", action="store_true", help="Disable desktop sleep prevention (caffeinate/wake-lock)")
    parser.add_argument("--cli", action="store_true", help="Run purely in Terminal / CLI mode without launching the Web UI")
    parser.add_argument("--no-browser", action="store_true", help="Run Web UI server without automatically opening browser")
    parser.add_argument("--port", type=int, default=8000, help="Port for the Animated AI Bot Agent Web UI (default: 8000)")
    args = parser.parse_args()

    bot = WakeUpBot()

    if args.test_notification:
        print("[Test] Sending desktop notification...")
        show_desktop_notification("🌅 Wake Up Bot Test", "Desktop notification is functioning properly!")
        print("[Test] Notification sent.")
        return

    if args.test_alarm:
        print("[Test] Ringing alarm for 5 seconds...")
        bot.alarm.start_ringing()
        time.sleep(5)
        bot.alarm.stop_ringing()
        print("[Test] Done.")
        return

    if args.test_news:
        print("[Test] Fetching latest English news via Gemini / RSS...")
        speech = get_morning_news_speech()
        print(f"[News Briefing]:\n{speech}\n")
        bot.voice.speak(speech)
        return

    if args.status:
        now = bot.get_current_time()
        secs, target = bot.get_seconds_until_next_alarm()
        print(f"Platform:               {bot.platform_name}")
        print(f"Current Time (GMT+5:30): {now.strftime('%Y-%m-%d %I:%M:%S %p')}")
        print(f"Next 6:00 AM Alarm:     {target.strftime('%Y-%m-%d %I:%M:%S %p')}")
        print(f"Time Remaining:         {int(secs//3600)}h {int((secs%3600)//60)}m {int(secs%60)}s")
        return

    if args.now:
        print("[Test] Triggering morning routine immediately...")
        bot.trigger_morning_routine()
        return

    # Start Animated AI Agent Web UI server unless --cli is explicitly passed
    if not args.cli:
        from src.server.web import start_web_server
        try:
            server = start_web_server(bot=bot, port=args.port, open_browser=not args.no_browser)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
        except Exception as e:
            print(f"[Web UI Notice]: Could not start Web UI server: {e}. Falling back to CLI mode.")

    # Normal scheduled mode
    try:
        bot.run_scheduler(prevent_sleep=not args.no_sleep_lock)
    except KeyboardInterrupt:
        print("\n[Bot] Shutting down gracefully. Have a great day!")
        sys.exit(0)


if __name__ == "__main__":
    main()
