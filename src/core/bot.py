"""Main Bot Orchestrator: Manages scheduling, alarms, voice interaction, and morning news."""
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.audio.alarm import AlarmController
from src.audio.voice import VoiceEngine
from src.core.config import (
    ALARM_HOUR,
    ALARM_MINUTE,
    GREETING_RESPONSE,
    GREETING_TRIGGER,
    TIMEZONE,
    USER_TITLE,
)
from src.platform_util.desktop import (
    DesktopSleepPreventer,
    get_platform_name,
    set_terminal_title,
    show_desktop_notification,
)
from src.services.news import get_morning_news_speech
from src.services.weather import get_current_weather


class WakeUpBot:
    """Manages scheduling, alarm ringer, voice interaction, and morning news briefings."""

    def __init__(self):
        self.tz = ZoneInfo(TIMEZONE)
        self.alarm = AlarmController()
        self.voice = VoiceEngine()
        self.sleep_preventer = DesktopSleepPreventer()
        self.platform_name = get_platform_name()

    def speak_welcome_greeting(self, blocking: bool = True) -> str:
        """Speaks the opening greeting: 'Hello Boss, how may I help you?'"""
        welcome_text = f"Hello {USER_TITLE}, how may I help you?"
        self.voice.speak(welcome_text, blocking=blocking)
        return welcome_text

    def get_current_time(self) -> datetime:
        """Returns current localized datetime in GMT +5:30."""
        return datetime.now(self.tz)

    def get_seconds_until_next_alarm(self) -> float:
        """Calculates precise seconds until next 6:00 AM in GMT+5:30."""
        now = self.get_current_time()
        target = now.replace(
            hour=ALARM_HOUR,
            minute=ALARM_MINUTE,
            second=0,
            microsecond=0
        )
        if target <= now:
            target += timedelta(days=1)

        delta = (target - now).total_seconds()
        return delta, target

    def trigger_morning_routine(self):
        """Executes the alarm and conversational assistant workflow."""
        set_terminal_title("⏰ 6:00 AM WAKE UP BOT - ALARM ACTIVE")
        print("\n==========================================")
        print(f"⏰ [WAKE UP BOT ACTIVATED] Time: {self.get_current_time().strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
        print(f"🖥️  Platform: {self.platform_name}")
        print("==========================================")

        # 1. Start ringing the device alarm
        self.alarm.start_ringing()

        # 2. Wait for user to greet "Good morning"
        print(f"[Bot] Waiting for greeting ('{GREETING_TRIGGER}') to silence alarm...")
        greeted = False
        start_time = time.time()

        while not greeted:
            user_input = self.voice.listen("Say 'Good morning' (or type and press Enter) to turn off the alarm: ")
            cleaned = user_input.strip().lower()

            if GREETING_TRIGGER in cleaned or "morning" in cleaned:
                greeted = True
                self.alarm.stop_ringing()
            elif any(w in cleaned for w in ["stop", "off", "dismiss", "wake up", "quit"]):
                greeted = True
                self.alarm.stop_ringing()
            elif cleaned == "":
                greeted = True
                self.alarm.stop_ringing()

            # Prevent endless loop if unattended (timeout after 2 minutes)
            if time.time() - start_time > 120:
                print("[Bot] Alarm timeout reached.")
                self.alarm.stop_ringing()
                break

        # 3. Respond with configured greeting
        set_terminal_title("🌅 Wake Up Bot - Morning Assistant")
        self.voice.speak(GREETING_RESPONSE)

        # 4. Morning Assistant Interaction Loop
        while True:
            command = self.voice.listen(
                f"What would you like me to do, {USER_TITLE}? (e.g. 'latest news' or 'that is all')"
            )
            cleaned_cmd = command.strip().lower()

            if any(keyword in cleaned_cmd for keyword in ["news", "headline", "headlines", "latest"]):
                show_desktop_notification("📰 Morning News Briefing", "Fetching and reading today's top English headlines.")
                self.voice.speak(f"Fetching the latest English news for you, {USER_TITLE}...")
                speech_text = get_morning_news_speech()
                self.voice.speak(speech_text)
                self.voice.speak(f"Is there anything else I can help you with, {USER_TITLE}?")
            elif any(keyword in cleaned_cmd for keyword in ["weather", "temperature", "forecast", "climate", "rain", "umbrella"]):
                show_desktop_notification("⛅ Today's Weather", "Fetching today's weather forecast...")
                self.voice.speak(f"Checking today's weather for you, {USER_TITLE}...")
                weather_data = get_current_weather()
                self.voice.speak(weather_data["spoken_text"])
                self.voice.speak(f"Is there anything else I can help you with, {USER_TITLE}?")
            elif any(keyword in cleaned_cmd for keyword in ["no", "that's all", "that is all", "stop", "exit", "thank you", "thanks", "bye"]):
                self.voice.speak(f"Have an awesome and productive day ahead, {USER_TITLE}!")
                break
            elif cleaned_cmd == "":
                continue
            else:
                self.voice.speak(
                    f"I heard: '{command}'. You can ask me to 'read the latest news', or say 'that is all' to finish."
                )

        set_terminal_title("🌅 Wake Up Bot - Standby")
        print("[Bot] Morning routine completed. Resuming daily watch.")

    def run_scheduler(self, prevent_sleep: bool = True):
        """Continuously monitors time and triggers routine every day at 6:00 AM IST."""
        set_terminal_title("🌅 Wake Up Bot - Monitoring (Daily 6:00 AM IST)")
        print("\n==========================================")
        print("🌅 Wake Up & Morning Assistant Bot")
        print(f"🖥️  Platform: {self.platform_name}")
        print(f"🌐 Timezone: {TIMEZONE} (GMT+5:30)")
        print(f"⏰ Daily Wake-Up Time: {ALARM_HOUR:02d}:{ALARM_MINUTE:02d} AM IST")
        print("==========================================\n")

        if prevent_sleep:
            self.sleep_preventer.activate()

        try:
            while True:
                seconds_remaining, next_target = self.get_seconds_until_next_alarm()
                hours = int(seconds_remaining // 3600)
                minutes = int((seconds_remaining % 3600) // 60)
                seconds = int(seconds_remaining % 60)

                print(f"[Schedule] Next alarm in {hours}h {minutes}m {seconds}s (at {next_target.strftime('%Y-%m-%d %I:%M:%S %p')})")

                if seconds_remaining > 5:
                    time.sleep(min(seconds_remaining - 1, 60))
                else:
                    time.sleep(max(seconds_remaining, 0))
                    self.trigger_morning_routine()
                    time.sleep(60)
        finally:
            if prevent_sleep:
                self.sleep_preventer.deactivate()
