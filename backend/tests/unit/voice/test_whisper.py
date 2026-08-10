import pytest

from jarvis.core.exceptions import ValidationError
from jarvis.voice.providers.whisper import FasterWhisperSTTProvider


class _FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeWhisperModel:
    def __init__(self, segments: list[str]) -> None:
        self._segments = [_FakeSegment(text) for text in segments]
        self.received_audio: bytes | None = None

    def transcribe(self, audio_file: object) -> tuple[list[_FakeSegment], object]:
        self.received_audio = audio_file.getvalue()  # type: ignore[attr-defined]
        return self._segments, object()


@pytest.mark.asyncio
async def test_transcribe_joins_segment_texts() -> None:
    model = _FakeWhisperModel([" hello ", "world "])
    provider = FasterWhisperSTTProvider(model)

    text = await provider.transcribe(b"fake-audio-bytes")

    assert text == "hello world"


@pytest.mark.asyncio
async def test_transcribe_passes_audio_bytes_through() -> None:
    model = _FakeWhisperModel(["hi"])
    provider = FasterWhisperSTTProvider(model)

    await provider.transcribe(b"fake-audio-bytes")

    assert model.received_audio == b"fake-audio-bytes"


@pytest.mark.asyncio
async def test_transcribe_rejects_empty_audio() -> None:
    provider = FasterWhisperSTTProvider(_FakeWhisperModel([]))

    with pytest.raises(ValidationError):
        await provider.transcribe(b"")
