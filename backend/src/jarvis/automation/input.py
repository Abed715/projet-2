"""Keyboard/mouse control behind an `InputBackend` Protocol. `pyautogui`
crashes at *import* time when no `$DISPLAY` is set (it eagerly constructs an
X11 `Display` handle in a submodule), so the real backend imports it lazily
inside `__init__`, never at module scope — see `automation/README.md`.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from jarvis.core.exceptions import ConfigurationError


class InputBackend(Protocol):
    def move_mouse(self, x: int, y: int) -> None: ...
    def click(self) -> None: ...
    def type_text(self, text: str) -> None: ...
    def press_key(self, key: str) -> None: ...


class PyAutoGuiInputBackend:
    """Real backend. Constructed lazily by callers only when a display is
    actually available — the constructor itself is what fails headlessly,
    so it's wrapped here rather than left to surface pyautogui's own
    `KeyError`/`Exception` types.
    """

    def __init__(self) -> None:
        try:
            import pyautogui
        except Exception as exc:  # pyautogui raises KeyError, not ImportError, headlessly
            raise ConfigurationError("no display available for input control") from exc
        self._pyautogui: Any = pyautogui

    def move_mouse(self, x: int, y: int) -> None:
        self._pyautogui.moveTo(x, y)

    def click(self) -> None:
        self._pyautogui.click()

    def type_text(self, text: str) -> None:
        self._pyautogui.typewrite(text)

    def press_key(self, key: str) -> None:
        self._pyautogui.press(key)


class InputService:
    def __init__(self, backend: InputBackend) -> None:
        self._backend = backend

    async def move_mouse(self, x: int, y: int) -> None:
        await asyncio.to_thread(self._backend.move_mouse, x, y)

    async def click(self) -> None:
        await asyncio.to_thread(self._backend.click)

    async def type_text(self, text: str) -> None:
        await asyncio.to_thread(self._backend.type_text, text)

    async def press_key(self, key: str) -> None:
        await asyncio.to_thread(self._backend.press_key, key)
