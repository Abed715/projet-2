"""Clipboard access behind a `ClipboardBackend` Protocol so tests never
touch a real clipboard mechanism (xclip/xsel/wl-clipboard on Linux), which
may not exist in headless environments — see `automation/README.md`.
"""

from __future__ import annotations

import asyncio
from typing import Protocol

import pyperclip

from jarvis.core.exceptions import ConfigurationError


class ClipboardBackend(Protocol):
    def read(self) -> str: ...
    def write(self, text: str) -> None: ...


class PyperclipClipboardBackend:
    """Real backend. `pyperclip` is safe to import at module scope — it
    only fails when `read`/`write` are actually called without a clipboard
    mechanism available.
    """

    def read(self) -> str:
        try:
            return str(pyperclip.paste())
        except pyperclip.PyperclipException as exc:
            raise ConfigurationError("no clipboard mechanism available") from exc

    def write(self, text: str) -> None:
        try:
            pyperclip.copy(text)
        except pyperclip.PyperclipException as exc:
            raise ConfigurationError("no clipboard mechanism available") from exc


class ClipboardService:
    def __init__(self, backend: ClipboardBackend) -> None:
        self._backend = backend

    async def read(self) -> str:
        return await asyncio.to_thread(self._backend.read)

    async def write(self, text: str) -> None:
        await asyncio.to_thread(self._backend.write, text)
