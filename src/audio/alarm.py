"""Alarm Controller: Rings alarm across macOS, Windows, Linux, and Android (Termux / ADB)."""
import math
import os
import platform
import shutil
import struct
import subprocess
import threading
import time
import wave

try:
    from src.core.config import ALARM_FILE
    from src.platform_util.desktop import is_termux, show_desktop_notification
except ImportError:
    from config import ALARM_FILE
    from desktop_helper import is_termux, show_desktop_notification

# Check for Windows winsound
IS_WINDOWS = platform.system() == "Windows"
winsound = None
if IS_WINDOWS:
    try:
        import winsound
    except ImportError:
        winsound = None


def generate_default_alarm_sound(file_path: str, duration_sec: float = 2.0):
    """
    Generates a high-pitch pulsing alarm tone WAV file using pure standard library
    so no external audio assets or downloads are required.
    """
    if os.path.exists(file_path):
        return

    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

    sample_rate = 44100
    total_frames = int(sample_rate * duration_sec)
    freq1 = 880   # A5 note
    freq2 = 1760  # A6 note

    with wave.open(file_path, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(total_frames):
            t = float(i) / sample_rate
            beep_phase = math.floor(t * 4) % 2
            if beep_phase == 0:
                amplitude = 0.5 * 32767
                val = int(amplitude * math.sin(2.0 * math.pi * freq1 * t))
            else:
                amplitude = 0.3 * 32767
                val = int(amplitude * math.sin(2.0 * math.pi * freq2 * t))

            frames.extend(struct.pack("<h", val))

        wav_file.writeframes(frames)


class AlarmController:
    """Controls ringing and stopping alarms across Desktop (macOS / Windows / Linux) and Android."""

    def __init__(self):
        self.is_ringing = False
        self._thread = None
        self.is_termux = is_termux()
        self.has_adb = shutil.which("adb") is not None

        # Ensure default alarm sound exists
        generate_default_alarm_sound(ALARM_FILE)

    def trigger_android_intent_alarm(self, hour: int = 6, minute: int = 0):
        """
        Attempts to launch the native Android Clock Alarm via Android Intent.
        Works in Termux (`am start`) or from PC via `adb` (if a device is connected).
        """
        intent_cmd = [
            "am", "start",
            "-a", "android.intent.action.SET_ALARM",
            "--ei", "android.intent.extra.HOUR", str(int(hour)),
            "--ei", "android.intent.extra.MINUTES", str(int(minute)),
            "--ez", "android.intent.extra.SKIP_UI", "true"
        ]

        if self.is_termux:
            try:
                subprocess.run(intent_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                print("[Alarm] Triggered native Android alarm via intent.")
            except Exception:
                pass
        elif self.has_adb:
            try:
                res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3)
                lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                if len(lines) > 1 and any("\tdevice" in line for line in lines[1:]):
                    subprocess.run(["adb", "shell"] + intent_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                    print("[Alarm] Triggered native Android alarm via connected ADB device.")
            except Exception:
                pass

    def _ring_loop(self):
        """Background loop that continuously plays alarm sound until stopped."""
        print("[Alarm] *** ⏰ ALARM IS RINGING! WAKE UP! ***")

        if self.is_termux and shutil.which("termux-volume"):
            try:
                subprocess.run(["termux-volume", "alarm", "15"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except Exception:
                pass

        while self.is_ringing:
            # 1. Android Termux native media player
            if self.is_termux and shutil.which("termux-media-player"):
                if shutil.which("termux-vibrate"):
                    subprocess.run(["termux-vibrate", "-t", "500", "-f"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                subprocess.run(["termux-media-player", "play", ALARM_FILE], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                time.sleep(2.0)

            # 2. Windows Desktop: winsound
            elif IS_WINDOWS and winsound:
                try:
                    winsound.PlaySound(ALARM_FILE, winsound.SND_FILENAME)
                except Exception:
                    ps_cmd = "$player = New-Object Media.SoundPlayer $args[0]; $player.PlaySync()"
                    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd, ALARM_FILE],
                                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            # 3. macOS Desktop: native afplay
            elif shutil.which("afplay"):
                subprocess.run(["afplay", ALARM_FILE], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            # 4. Linux Desktop: ALSA aplay
            elif shutil.which("aplay"):
                subprocess.run(["aplay", ALARM_FILE], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            # 5. Linux Desktop: PulseAudio paplay
            elif shutil.which("paplay"):
                subprocess.run(["paplay", ALARM_FILE], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            # 6. Terminal bell / beep fallback
            else:
                print("\a", end="", flush=True)
                time.sleep(0.5)

    def start_ringing(self):
        """Starts the continuous ringing process across desktop & mobile."""
        if not self.is_ringing:
            self.is_ringing = True
            show_desktop_notification("🌅 6:00 AM Wake-Up Alarm", "Time to wake up! Say 'Good morning' or press Enter.")
            self.trigger_android_intent_alarm()
            self._thread = threading.Thread(target=self._ring_loop, daemon=True)
            self._thread.start()

    def stop_ringing(self):
        """Stops the alarm immediately across all platforms."""
        self.is_ringing = False

        if IS_WINDOWS and winsound:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

        if self.is_termux and shutil.which("termux-media-player"):
            try:
                subprocess.run(["termux-media-player", "stop"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except Exception:
                pass

        print("[Alarm] Alarm has been turned off.")


if __name__ == "__main__":
    alarm = AlarmController()
    print("Testing alarm for 3 seconds...")
    alarm.start_ringing()
    time.sleep(3)
    alarm.stop_ringing()
    print("Test finished.")
