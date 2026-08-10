"""`faster-whisper` adapter for the `STTProvider` protocol.

`model` is typed `Any` rather than the real `faster_whisper.WhisperModel`
class so tests can substitute a lightweight double exposing only
`transcribe(...)` — the real model satisfies that shape at runtime. This
also means unit tests never load real Whisper weights (a multi-hundred-MB
download on first use); see `voice/README.md`.
"""

from __future__ import annotations

import asyncio
import io
from typing import Any

from jarvis.core.exceptions import ValidationError
from jarvis.voice.providers.base import STTProvider

DEFAULT_MODEL_SIZE = "small"


class FasterWhisperSTTProvider:
    def __init__(self, model: Any) -> None:
        self._model = model

    async def transcribe(self, audio: bytes) -> str:
        if not audio:
            raise ValidationError("audio must not be empty")

        def _run() -> str:
            segments, _info = self._model.transcribe(io.BytesIO(audio))
            return " ".join(segment.text.strip() for segment in segments).strip()

        return await asyncio.to_thread(_run)


_whisper_provider_satisfies_protocol: type[STTProvider] = FasterWhisperSTTProvider
