import pytest

from jarvis.core.exceptions import ConfigurationError
from jarvis.vision.window_detection import (
    WindowDetectionService,
    WindowInfo,
    WmctrlWindowDetectionBackend,
)


class _FakeWindowDetectionBackend:
    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail

    def list_windows(self) -> list[WindowInfo]:
        if self._fail:
            raise ConfigurationError("wmctrl is not available on this system")
        return [WindowInfo(window_id="0x1", title="Terminal")]


@pytest.mark.asyncio
async def test_list_windows_returns_backend_windows() -> None:
    service = WindowDetectionService(_FakeWindowDetectionBackend())

    windows = await service.list_windows()

    assert windows == [WindowInfo(window_id="0x1", title="Terminal")]


@pytest.mark.asyncio
async def test_list_windows_propagates_configuration_error() -> None:
    service = WindowDetectionService(_FakeWindowDetectionBackend(fail=True))

    with pytest.raises(ConfigurationError):
        await service.list_windows()


def test_wmctrl_backend_raises_configuration_error_when_missing() -> None:
    # This sandbox has no wmctrl binary installed.
    with pytest.raises(ConfigurationError):
        WmctrlWindowDetectionBackend().list_windows()
