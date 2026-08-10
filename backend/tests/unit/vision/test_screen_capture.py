import pytest

from jarvis.core.exceptions import ConfigurationError
from jarvis.vision.screen_capture import MssScreenCaptureBackend, ScreenCaptureService


class _FakeScreenCaptureBackend:
    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail

    def capture(self) -> bytes:
        if self._fail:
            raise ConfigurationError("no display available for screen capture")
        return b"fake-png-bytes"


@pytest.mark.asyncio
async def test_capture_returns_backend_bytes() -> None:
    service = ScreenCaptureService(_FakeScreenCaptureBackend())

    assert await service.capture() == b"fake-png-bytes"


@pytest.mark.asyncio
async def test_capture_propagates_configuration_error() -> None:
    service = ScreenCaptureService(_FakeScreenCaptureBackend(fail=True))

    with pytest.raises(ConfigurationError):
        await service.capture()


def test_mss_backend_raises_configuration_error_without_display() -> None:
    # This sandbox has no display server, so mss.mss() construction fails —
    # capture() must translate that into a ConfigurationError.
    with pytest.raises(ConfigurationError):
        MssScreenCaptureBackend().capture()
