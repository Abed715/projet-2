"""Open-window listing behind a `WindowDetectionBackend` Protocol. The real
backend shells out to `wmctrl` (X11 window manager control) — like
`notify-send` in `automation.notifications`, it may simply not be
installed, so its availability is checked up front rather than left to
fail opaquely. See `vision/README.md`.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from dataclasses import dataclass
from typing import Protocol

from jarvis.core.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class WindowInfo:
    window_id: str
    title: str


class WindowDetectionBackend(Protocol):
    def list_windows(self) -> list[WindowInfo]: ...


class WmctrlWindowDetectionBackend:
    """Real backend, X11/`wmctrl` only for now."""

    def list_windows(self) -> list[WindowInfo]:
        if shutil.which("wmctrl") is None:
            raise ConfigurationError("wmctrl is not available on this system")

        result = subprocess.run(  # noqa: S603
            ["wmctrl", "-l"], check=True, capture_output=True, text=True
        )
        windows = []
        for line in result.stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) == 4:
                windows.append(WindowInfo(window_id=parts[0], title=parts[3]))
        return windows


class WindowDetectionService:
    def __init__(self, backend: WindowDetectionBackend) -> None:
        self._backend = backend

    async def list_windows(self) -> list[WindowInfo]:
        return await asyncio.to_thread(self._backend.list_windows)
