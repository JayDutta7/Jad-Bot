"""Desktop Helper: Provides cross-platform OS detection, desktop notifications,
sleep prevention (wake-locks), and secure system interaction for macOS, Windows, Linux, and Android.
"""
import ctypes
import os
import platform
import re
import shutil
import subprocess
import sys
from typing import Optional


def is_termux() -> bool:
    """Checks if currently running in Android Termux environment."""
    return (
        "com.termux" in os.environ.get("PREFIX", "")
        or shutil.which("termux-api") is not None
        or shutil.which("termux-media-player") is not None
    )


def get_platform_name() -> str:
    """Returns a friendly description of the host platform."""
    if is_termux():
        return "Android (Termux)"
    system = platform.system()
    if system == "Darwin":
        mac_ver = platform.mac_ver()[0]
        return f"macOS Desktop (Version {mac_ver})" if mac_ver else "macOS Desktop"
    elif system == "Windows":
        win_ver = platform.version()
        return f"Windows Desktop (Build {win_ver})"
    elif system == "Linux":
        return "Linux Desktop / Server"
    return f"{system} OS"


def set_terminal_title(title: str):
    """
    Sets the terminal window / tab title securely cross-platform.
    Uses Windows API SetConsoleTitleW or ANSI escape sequences without invoking a shell.
    """
    try:
        # Strip newlines and control characters to prevent ANSI escape injection
        clean_title = re.sub(r'[\r\n\x00-\x1f\x7f]', '', title)[:256]

        if platform.system() == "Windows":
            windll = getattr(ctypes, "windll", None)
            if windll and hasattr(windll.kernel32, "SetConsoleTitleW"):
                windll.kernel32.SetConsoleTitleW(clean_title)
                return

        # Unix / ANSI terminal escape sequence
        sys.stdout.write(f"\033]0;{clean_title}\007")
        sys.stdout.flush()
    except Exception:
        pass


def show_desktop_notification(title: str, message: str):
    """
    Displays a native desktop banner/toast notification on macOS, Windows, Linux, or Android.
    Hardened against command injection by using argument binding rather than shell string interpolation.
    """
    try:
        # Sanitize length to prevent buffer overruns
        clean_title = str(title)[:128]
        clean_msg = str(message)[:256]

        # 1. Android Termux notification
        if is_termux() and shutil.which("termux-notification"):
            subprocess.run(
                ["termux-notification", "--title", clean_title, "--content", clean_msg, "--priority", "high"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return

        system = platform.system()

        # 2. macOS notification via AppleScript using run argv parameter binding
        if system == "Darwin" and shutil.which("osascript"):
            script = (
                "on run argv\n"
                "  display notification (item 2 of argv) with title (item 1 of argv) sound name \"Glass\"\n"
                "end run"
            )
            subprocess.run(
                ["osascript", "-e", script, clean_title, clean_msg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return

        # 3. Windows notification via PowerShell using parameter binding ($args)
        if system == "Windows":
            ps_script = (
                "[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); "
                "$notify = New-Object System.Windows.Forms.NotifyIcon; "
                "$notify.Icon = [System.Drawing.SystemIcons]::Information; "
                "$notify.BalloonTipTitle = $args[0]; "
                "$notify.BalloonTipText = $args[1]; "
                "$notify.Visible = $True; "
                "$notify.ShowBalloonTip(10000); "
                "Start-Sleep -Milliseconds 800; "
                "$notify.Dispose();"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script, clean_title, clean_msg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return

        # 4. Linux desktop notification via notify-send
        if system == "Linux" and shutil.which("notify-send"):
            subprocess.run(
                ["notify-send", "-u", "critical", clean_title, clean_msg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
            return

    except Exception:
        # Non-critical feature; fail silently
        pass


class DesktopSleepPreventer:
    """
    Prevents desktop (macOS / Windows) from sleeping while the bot waits overnight for 6:00 AM.
    - macOS: Spawns built-in `caffeinate` tied to current process PID.
    - Windows: Uses Windows API `SetThreadExecutionState` via ctypes.
    - Android: Uses `termux-wake-lock`.
    """

    def __init__(self):
        self._caffeinate_proc: Optional[subprocess.Popen] = None
        self._is_active = False

    def activate(self):
        """Activates wake lock / sleep prevention."""
        if self._is_active:
            return

        try:
            # 1. Android Termux
            if is_termux() and shutil.which("termux-wake-lock"):
                subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._is_active = True
                print("[WakeLock] Android Termux wake-lock active.")
                return

            system = platform.system()

            # 2. macOS Desktop: Caffeinate
            if system == "Darwin" and shutil.which("caffeinate"):
                pid = str(os.getpid())
                self._caffeinate_proc = subprocess.Popen(
                    ["caffeinate", "-dimsu", "-w", pid],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self._is_active = True
                print("[WakeLock] macOS caffeinate active (prevents Mac sleep overnight).")
                return

            # 3. Windows Desktop: SetThreadExecutionState
            if system == "Windows":
                try:
                    windll = getattr(ctypes, "windll", None)
                    if windll:
                        ES_CONTINUOUS = 0x80000000
                        ES_SYSTEM_REQUIRED = 0x00000001
                        ES_DISPLAY_REQUIRED = 0x00000002
                        windll.kernel32.SetThreadExecutionState(
                            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                        )
                        self._is_active = True
                        print("[WakeLock] Windows SetThreadExecutionState active (prevents PC sleep overnight).")
                        return
                except Exception as e:
                    print(f"[WakeLock Notice]: Could not set Windows execution state: {e}")

        except Exception as e:
            print(f"[WakeLock Notice]: {e}")

    def deactivate(self):
        """Deactivates sleep prevention and restores default power behavior."""
        if not self._is_active:
            return

        try:
            # Android
            if is_termux() and shutil.which("termux-wake-unlock"):
                subprocess.run(["termux-wake-unlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # macOS
            if self._caffeinate_proc:
                self._caffeinate_proc.terminate()
                self._caffeinate_proc = None

            # Windows
            if platform.system() == "Windows":
                try:
                    windll = getattr(ctypes, "windll", None)
                    if windll:
                        ES_CONTINUOUS = 0x80000000
                        windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self._is_active = False
            print("[WakeLock] Desktop power management restored to normal.")
