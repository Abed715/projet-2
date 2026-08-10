import io
import wave

import pytest

from jarvis.core.exceptions import ValidationError
from jarvis.voice.providers.piper import PiperTTSProvider


class _FakePiperVoice:
    def __init__(self) -> None:
        self.received_text: str | None = None

    def synthesize_wav(self, text: str, wav_file: wave.Wave_write) -> None:
        self.received_text = text
        wav_file.writeframes(b"\x00\x01" * 10)


@pytest.mark.asyncio
async def test_synthesize_returns_valid_wav_bytes() -> None:
    voice = _FakePiperVoice()
    provider = PiperTTSProvider(voice)

    audio = await provider.synthesize("hello there")

    assert voice.received_text == "hello there"
    with wave.open(io.BytesIO(audio), "rb") as wav_file:
        assert wav_file.getnframes() == 10


@pytest.mark.asyncio
async def test_synthesize_rejects_empty_text() -> None:
    provider = PiperTTSProvider(_FakePiperVoice())

    with pytest.raises(ValidationError):
        await provider.synthesize("")


@pytest.mark.asyncio
async def test_synthesize_rejects_whitespace_only_text() -> None:
    provider = PiperTTSProvider(_FakePiperVoice())

    with pytest.raises(ValidationError):
        await provider.synthesize("   ")
