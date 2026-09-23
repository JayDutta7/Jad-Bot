"""Platform utilities package."""
from .desktop import (
    DesktopSleepPreventer,
    get_platform_name,
    is_termux,
    set_terminal_title,
    show_desktop_notification,
)

__all__ = [
    "is_termux",
    "get_platform_name",
    "set_terminal_title",
    "show_desktop_notification",
    "DesktopSleepPreventer",
]
