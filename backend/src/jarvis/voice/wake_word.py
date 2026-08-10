"""Wake-word detection behind a `WakeWordDetector` Protocol, following the
same swappable-backend pattern as `automation`/`vision`'s OS-level
services — the real model (`openwakeword`) needs pretrained weights
downloaded separately, so tests inject a fake detector instead of loading
real weights. See `voice/README.md`.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from jarvis.core.exceptions import ValidationError

DEFAULT_THRESHOLD = 0.5


class WakeWordDetector(Protocol):
    async def detect(self, audio_frame: bytes) -> bool: ...


class OpenWakeWordDetector:
    """Real detector. `model` is typed `Any` — see `providers/whisper.py`'s
    docstring for why (same reasoning, same test-double pattern).
    """

    def __init__(self, model: Any, *, wake_word: str, threshold: float = DEFAULT_THRESHOLD) -> None:
        self._model = model
        self._wake_word = wake_word
        self._threshold = threshold

    async def detect(self, audio_frame: bytes) -> bool:
        if not audio_frame:
            raise ValidationError("audio_frame must not be empty")

        def _run() -> bool:
            import numpy as np

            samples = np.frombuffer(audio_frame, dtype=np.int16)
            scores = self._model.predict(samples)
            return bool(scores.get(self._wake_word, 0.0) >= self._threshold)

        return await asyncio.to_thread(_run)


_open_wake_word_satisfies_protocol: type[WakeWordDetector] = OpenWakeWordDetector
