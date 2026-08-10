"""`piper-tts` adapter for the `TTSProvider` protocol.

`voice` is typed `Any` rather than the real `piper.PiperVoice` class so
tests can substitute a lightweight double exposing only
`synthesize_wav(...)` — the real voice model satisfies that shape at
runtime. This also means unit tests never load a real Piper voice model
(an `.onnx` file the deployment must supply); see `voice/README.md`.
"""

from __future__ import annotations

import asyncio
import io
import wave
from typing import Any

from jarvis.core.exceptions import ValidationError
from jarvis.voice.providers.base import TTSProvider

_SAMPLE_WIDTH_BYTES = 2
_CHANNELS = 1
_SAMPLE_RATE_HZ = 22050


class PiperTTSProvider:
    def __init__(self, voice: Any) -> None:
        self._voice = voice

    async def synthesize(self, text: str) -> bytes:
        if not text.strip():
            raise ValidationError("text must not be empty")

        def _run() -> bytes:
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(_CHANNELS)
                wav_file.setsampwidth(_SAMPLE_WIDTH_BYTES)
                wav_file.setframerate(_SAMPLE_RATE_HZ)
                self._voice.synthesize_wav(text, wav_file)
            return buffer.getvalue()

        return await asyncio.to_thread(_run)


_piper_provider_satisfies_protocol: type[TTSProvider] = PiperTTSProvider
