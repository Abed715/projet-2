import pytest

from jarvis.core.exceptions import ValidationError
from jarvis.voice.wake_word import OpenWakeWordDetector


class _FakeWakeWordModel:
    def __init__(self, scores: dict[str, float]) -> None:
        self._scores = scores
        self.received_samples: object = None

    def predict(self, samples: object) -> dict[str, float]:
        self.received_samples = samples
        return self._scores


@pytest.mark.asyncio
async def test_detect_returns_true_above_threshold() -> None:
    model = _FakeWakeWordModel({"hey_jarvis": 0.9})
    detector = OpenWakeWordDetector(model, wake_word="hey_jarvis", threshold=0.5)

    assert await detector.detect(b"\x00\x01" * 100) is True


@pytest.mark.asyncio
async def test_detect_returns_false_below_threshold() -> None:
    model = _FakeWakeWordModel({"hey_jarvis": 0.1})
    detector = OpenWakeWordDetector(model, wake_word="hey_jarvis", threshold=0.5)

    assert await detector.detect(b"\x00\x01" * 100) is False


@pytest.mark.asyncio
async def test_detect_returns_false_when_wake_word_absent_from_scores() -> None:
    model = _FakeWakeWordModel({"some_other_word": 0.99})
    detector = OpenWakeWordDetector(model, wake_word="hey_jarvis", threshold=0.5)

    assert await detector.detect(b"\x00\x01" * 100) is False


@pytest.mark.asyncio
async def test_detect_rejects_empty_audio_frame() -> None:
    detector = OpenWakeWordDetector(_FakeWakeWordModel({}), wake_word="hey_jarvis")

    with pytest.raises(ValidationError):
        await detector.detect(b"")
