import sys

import pytest

from jarvis.automation.clipboard import ClipboardService
from jarvis.automation.input import InputService
from jarvis.automation.notifications import NotificationService
from jarvis.automation.process import ProcessService
from jarvis.automation.tools import register_automation_tools
from jarvis.brain.tools import ToolInvocationStatus, ToolRegistry
from jarvis.core.exceptions import ValidationError
from jarvis.security import InMemoryAuditLog, PermissionEngine, Role


class _FakeClipboardBackend:
    def __init__(self) -> None:
        self._text = ""

    def read(self) -> str:
        return self._text

    def write(self, text: str) -> None:
        self._text = text


class _FakeNotificationBackend:
    def send(self, *, title: str, message: str) -> None:
        pass


class _FakeInputBackend:
    def move_mouse(self, x: int, y: int) -> None:
        pass

    def click(self) -> None:
        pass

    def type_text(self, text: str) -> None:
        pass

    def press_key(self, key: str) -> None:
        pass


@pytest.fixture
def permission_engine() -> PermissionEngine:
    return PermissionEngine()


@pytest.fixture
def registry(permission_engine: PermissionEngine) -> ToolRegistry:
    audit_log = InMemoryAuditLog()
    registry = ToolRegistry(permission_engine, audit_log)
    register_automation_tools(
        registry,
        process=ProcessService(),
        clipboard=ClipboardService(_FakeClipboardBackend()),
        notifications=NotificationService(_FakeNotificationBackend()),
        input_service=InputService(_FakeInputBackend()),
    )
    return registry


def test_all_tools_registered(registry: ToolRegistry) -> None:
    names = {tool.name for tool in registry.list_tools()}
    assert names == {
        "list_processes",
        "open_application",
        "close_application",
        "clipboard_read",
        "clipboard_write",
        "send_notification",
        "mouse_move",
        "mouse_click",
        "type_text",
        "press_key",
    }


@pytest.mark.asyncio
async def test_list_processes_is_safe(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="list_processes",
        arguments={},
        role=Role.GUEST,
        session_id="s1",
        actor="automation",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert isinstance(result.result, dict)
    assert "processes" in result.result


@pytest.mark.asyncio
async def test_clipboard_write_then_read(
    registry: ToolRegistry, permission_engine: PermissionEngine
) -> None:
    permission_engine.grant_for_session("s1", "clipboard_write")
    permission_engine.grant_for_session("s1", "clipboard_read")

    write_result = await registry.invoke(
        name="clipboard_write",
        arguments={"text": "hi"},
        role=Role.OPERATOR,
        session_id="s1",
        actor="automation",
        correlation_id="c1",
    )
    assert write_result.status is ToolInvocationStatus.OK

    read_result = await registry.invoke(
        name="clipboard_read",
        arguments={},
        role=Role.OPERATOR,
        session_id="s1",
        actor="automation",
        correlation_id="c2",
    )
    assert read_result.result == {"text": "hi"}


@pytest.mark.asyncio
async def test_open_application_requires_confirmation(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="open_application",
        arguments={"command": [sys.executable, "-c", "print('hi')"]},
        role=Role.OWNER,
        session_id="s1",
        actor="automation",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.REQUIRES_CONFIRMATION


@pytest.mark.asyncio
async def test_open_application_rejects_non_list_command(
    registry: ToolRegistry, permission_engine: PermissionEngine
) -> None:
    permission_engine.grant_for_session("s1", "open_application")

    with pytest.raises(ValidationError):
        await registry.invoke(
            name="open_application",
            arguments={"command": "not a list"},
            role=Role.OWNER,
            session_id="s1",
            actor="automation",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_mouse_click_requires_confirmation(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="mouse_click",
        arguments={},
        role=Role.OWNER,
        session_id="s1",
        actor="automation",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.REQUIRES_CONFIRMATION


@pytest.mark.asyncio
async def test_send_notification_is_safe(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="send_notification",
        arguments={"title": "t", "message": "m"},
        role=Role.GUEST,
        session_id="s1",
        actor="automation",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
