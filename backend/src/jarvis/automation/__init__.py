"""jarvis.automation — computer control: process management, clipboard,
desktop notifications, and keyboard/mouse input, plus their tool
registrations.

See README.md for the full public interface and design notes.
"""

from jarvis.automation.clipboard import (
    ClipboardBackend,
    ClipboardService,
    PyperclipClipboardBackend,
)
from jarvis.automation.input import InputBackend, InputService, PyAutoGuiInputBackend
from jarvis.automation.notifications import (
    DesktopNotificationBackend,
    NotificationBackend,
    NotificationService,
)
from jarvis.automation.process import ProcessInfo, ProcessService
from jarvis.automation.tools import register_automation_tools

__all__ = [
    "ClipboardBackend",
    "ClipboardService",
    "DesktopNotificationBackend",
    "InputBackend",
    "InputService",
    "NotificationBackend",
    "NotificationService",
    "ProcessInfo",
    "ProcessService",
    "PyAutoGuiInputBackend",
    "PyperclipClipboardBackend",
    "register_automation_tools",
]
