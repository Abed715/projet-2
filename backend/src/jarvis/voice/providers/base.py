"""Speech provider abstraction: one interface per direction, swappable
backends — mirrors `brain.providers.base.LLMProvider`. Concrete adapters
(`FasterWhisperSTTProvider`, `PiperTTSProvider`) live alongside this module.
"""

from __future__ import annotations

from typing import Protocol


class STTProvider(Protocol):
    """Speech-to-text: raw audio bytes in, transcribed text out."""

    async def transcribe(self, audio: bytes) -> str: ...


class TTSProvider(Protocol):
    """Text-to-speech: text in, synthesized audio bytes (WAV) out."""

    async def synthesize(self, text: str) -> bytes: ...
