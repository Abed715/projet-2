import pytest

from jarvis.automation.notifications import NotificationService
from jarvis.core.exceptions import ConfigurationError


class _FakeNotificationBackend:
    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail
        self.sent: list[tuple[str, str]] = []

    def send(self, *, title: str, message: str) -> None:
        if self._fail:
            raise ConfigurationError("notify-send is not available on this system")
        self.sent.append((title, message))


@pytest.mark.asyncio
async def test_send_records_title_and_message() -> None:
    backend = _FakeNotificationBackend()
    service = NotificationService(backend)

    await service.send(title="Build done", message="All tests passed")

    assert backend.sent == [("Build done", "All tests passed")]


@pytest.mark.asyncio
async def test_send_propagates_configuration_error() -> None:
    service = NotificationService(_FakeNotificationBackend(fail=True))

    with pytest.raises(ConfigurationError):
        await service.send(title="x", message="y")
