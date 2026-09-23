import re
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from src.audio.alarm import AlarmController
from src.audio.voice import VoiceEngine
from src.core.config import (
    ALARM_HOUR,
    ALARM_MINUTE,
    GREETING_RESPONSE,
    GREETING_TRIGGER,
    SUNDAY_ALARM_HOUR,
    SUNDAY_ALARM_MINUTE,
    TIMEZONE,
    USER_TITLE,
    WAKE_RESPONSE,
    WAKE_WORDS,
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
        # Custom user-defined alarm override (if None, follows 6:30 AM weekdays / 7:00 AM Sunday)
        self.custom_alarm_hour: Optional[int] = None
        self.custom_alarm_minute: Optional[int] = None

    def speak_welcome_greeting(self, blocking: bool = True) -> str:
        """Speaks the opening greeting: 'Hello Boss, how may I help you?'"""
        welcome_text = f"Hello {USER_TITLE}, how may I help you?"
        self.voice.speak(welcome_text, blocking=blocking)
        return welcome_text

    def check_wake_word(self, user_text: str) -> Optional[str]:
        """Checks if user text triggers the wake word ('Hello Jad') and returns activation reply."""
        if self.voice.is_wake_word(user_text):
            return WAKE_RESPONSE
        return None

    def get_current_time(self) -> datetime:
        """Returns current localized datetime in GMT +5:30."""
        return datetime.now(self.tz)

    def get_alarm_time_for_date(self, target_date) -> Tuple[int, int, str]:
        """
        Determines the alarm hour, minute, and schedule description for a given date.
        If a custom alarm time is set by the user, that overrides default schedules.
        Otherwise:
          - Sunday (target_date.weekday() == 6): SUNDAY_ALARM_HOUR : SUNDAY_ALARM_MINUTE (7:00 AM)
          - Mon-Sat: ALARM_HOUR : ALARM_MINUTE (6:30 AM)
        """
        if self.custom_alarm_hour is not None and self.custom_alarm_minute is not None:
            period = "AM" if self.custom_alarm_hour < 12 else "PM"
            h12 = self.custom_alarm_hour % 12 or 12
            return (
                self.custom_alarm_hour,
                self.custom_alarm_minute,
                f"Custom Alarm ({h12}:{self.custom_alarm_minute:02d} {period})"
            )

        if target_date.weekday() == 6:  # Sunday
            return (SUNDAY_ALARM_HOUR, SUNDAY_ALARM_MINUTE, "Sunday Schedule (7:00 AM)")
        else:
            return (ALARM_HOUR, ALARM_MINUTE, "Weekday Schedule (6:30 AM)")

    def get_seconds_until_next_alarm(self) -> Tuple[float, datetime]:
        """
        Calculates precise seconds until next alarm in GMT+5:30.
        Respects default 6:30 AM weekdays, 7:00 AM Sundays, and custom user overrides.
        """
        now = self.get_current_time()

        # 1. Test today's alarm time
        h_today, m_today, _ = self.get_alarm_time_for_date(now.date())
        target = now.replace(
            hour=h_today,
            minute=m_today,
            second=0,
            microsecond=0
        )

        if target > now:
            delta = (target - now).total_seconds()
            return delta, target

        # 2. Today's alarm has passed, calculate for tomorrow
        tomorrow = (now + timedelta(days=1)).date()
        h_tom, m_tom, _ = self.get_alarm_time_for_date(tomorrow)
        target_tom = now.replace(
            year=tomorrow.year,
            month=tomorrow.month,
            day=tomorrow.day,
            hour=h_tom,
            minute=m_tom,
            second=0,
            microsecond=0
        )
        delta = (target_tom - now).total_seconds()
        return delta, target_tom

    def set_custom_alarm_time(self, hour: int, minute: int) -> str:
        """Sets a user-defined custom alarm time and returns confirmation text."""
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time: {hour:02d}:{minute:02d}")
        self.custom_alarm_hour = hour
        self.custom_alarm_minute = minute
        period = "AM" if hour < 12 else "PM"
        h12 = hour % 12 or 12
        time_str = f"{h12}:{minute:02d} {period}"
        return f"Alarm time has been updated to {time_str}, {USER_TITLE}."

    def reset_custom_alarm_time(self) -> str:
        """Resets alarm schedule back to default (6:30 AM Mon-Sat, 7:00 AM Sun)."""
        self.custom_alarm_hour = None
        self.custom_alarm_minute = None
        return f"Alarm schedule has been reset to default: 6:30 AM weekdays and 7:00 AM on Sundays, {USER_TITLE}."

    def parse_alarm_time_command(self, text: str) -> Optional[Tuple[str, Optional[int], Optional[int]]]:
        """
        Parses conversational user commands to change or reset alarm time.
        Returns ('reset', None, None) or ('set', hour_24, minute) or None.
        """
        t = text.lower().strip()
        if "reset" in t and ("alarm" in t or "schedule" in t or "default" in t or "time" in t):
            return ("reset", None, None)
        if "default alarm" in t or "default schedule" in t:
            return ("reset", None, None)

        # Match phrases like:
        # "set alarm to 7:30 am", "change alarm to 8 am", "wake me up at 6.30 am", "set alarm 7 am"
        match = re.search(
            r'(?:alarm|wake me up|wake up|time)(?:.*?(?:to|at|for|\bis\b))?\s*(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?',
            t
        )
        if not match:
            match = re.search(r'\b(?:at\s+)?(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)\b', t)

        if match:
            h = int(match.group(1))
            m = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3).lower() if match.group(3) else None

            if ampm == "pm" and h < 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
            elif ampm is None and 1 <= h <= 5:
                # e.g., "set alarm to 5" in morning wake up context usually means 5 AM
                pass

            if 0 <= h <= 23 and 0 <= m <= 59:
                return ("set", h, m)

        return None

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
