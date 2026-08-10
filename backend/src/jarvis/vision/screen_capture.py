"""Screenshot capture behind a `ScreenCaptureBackend` Protocol. `mss`
imports safely at module scope, but constructing `mss.mss()` — which opens
a connection to the display server — raises headlessly, so the real
backend defers that construction to `capture()`, not `__init__`, and wraps
the failure in `ConfigurationError`. See `vision/README.md`.
"""

from __future__ import annotations

import asyncio
from typing import Protocol

from jarvis.core.exceptions import ConfigurationError


class ScreenCaptureBackend(Protocol):
    def capture(self) -> bytes: ...


class MssScreenCaptureBackend:
    """Real backend. Captures the primary monitor and returns PNG bytes."""

    def capture(self) -> bytes:
        try:
            import mss
            import mss.tools
        except Exception as exc:
            raise ConfigurationError("no display available for screen capture") from exc

        try:
            with mss.MSS() as sct:
                shot = sct.grab(sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0])
                png_bytes = mss.tools.to_png(shot.rgb, shot.size)
        except Exception as exc:
            raise ConfigurationError("no display available for screen capture") from exc
        if png_bytes is None:
            raise ConfigurationError("screen capture produced no image data")
        return png_bytes


class ScreenCaptureService:
    def __init__(self, backend: ScreenCaptureBackend) -> None:
        self._backend = backend

    async def capture(self) -> bytes:
        return await asyncio.to_thread(self._backend.capture)
