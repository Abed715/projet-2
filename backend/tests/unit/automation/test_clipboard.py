import pytest

from jarvis.automation.clipboard import ClipboardService
from jarvis.core.exceptions import ConfigurationError


class _FakeClipboardBackend:
    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail
        self._text = ""

    def read(self) -> str:
        if self._fail:
            raise ConfigurationError("no clipboard mechanism available")
        return self._text

    def write(self, text: str) -> None:
        if self._fail:
            raise ConfigurationError("no clipboard mechanism available")
        self._text = text


@pytest.mark.asyncio
async def test_write_then_read_round_trips() -> None:
    service = ClipboardService(_FakeClipboardBackend())

    await service.write("hello jarvis")

    assert await service.read() == "hello jarvis"


@pytest.mark.asyncio
async def test_read_propagates_configuration_error() -> None:
    service = ClipboardService(_FakeClipboardBackend(fail=True))

    with pytest.raises(ConfigurationError):
        await service.read()


@pytest.mark.asyncio
async def test_write_propagates_configuration_error() -> None:
    service = ClipboardService(_FakeClipboardBackend(fail=True))

    with pytest.raises(ConfigurationError):
        await service.write("x")
