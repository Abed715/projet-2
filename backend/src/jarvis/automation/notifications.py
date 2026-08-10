"""Desktop notifications behind a `NotificationBackend` Protocol. The real
backend shells out to `notify-send` (Linux/libnotify) via the sandboxed
`security.SandboxExecutor` pattern's sibling — a plain `subprocess.run`,
since notifications aren't workspace-confined filesystem/shell actions.
macOS/Windows backends are deferred until there's a target to test against.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from typing import Protocol

from jarvis.core.exceptions import ConfigurationError


class NotificationBackend(Protocol):
    def send(self, *, title: str, message: str) -> None: ...


class DesktopNotificationBackend:
    """Real backend, Linux/libnotify only for now."""

    def send(self, *, title: str, message: str) -> None:
        if shutil.which("notify-send") is None:
            raise ConfigurationError("notify-send is not available on this system")
        subprocess.run(["notify-send", title, message], check=True)  # noqa: S603


class NotificationService:
    def __init__(self, backend: NotificationBackend) -> None:
        self._backend = backend

    async def send(self, *, title: str, message: str) -> None:
        await asyncio.to_thread(self._backend.send, title=title, message=message)
