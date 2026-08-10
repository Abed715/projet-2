"""Registers `automation`'s process/clipboard/notification/input
capabilities as tools in `brain`'s `ToolRegistry`, each tagged with the
risk level `security.rbac` enforces before it runs.
"""

from __future__ import annotations

from jarvis.automation.clipboard import ClipboardService
from jarvis.automation.input import InputService
from jarvis.automation.notifications import NotificationService
from jarvis.automation.process import ProcessService
from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import ValidationError
from jarvis.security import RiskLevel


def _require_str(arguments: dict[str, object], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str):
        raise ValidationError(f"{key!r} must be a string")
    return value


def _require_int(arguments: dict[str, object], key: str) -> int:
    value = arguments.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{key!r} must be an integer")
    return value


def register_automation_tools(
    registry: ToolRegistry,
    *,
    process: ProcessService,
    clipboard: ClipboardService,
    notifications: NotificationService,
    input_service: InputService,
) -> None:
    async def list_processes(arguments: dict[str, object]) -> object:
        return {
            "processes": [
                {"pid": p.pid, "name": p.name, "status": p.status}
                for p in await process.list_processes()
            ]
        }

    async def open_application(arguments: dict[str, object]) -> object:
        command = arguments.get("command")
        if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
            raise ValidationError("'command' must be a list of strings")
        pid = await process.open_application(command)
        return {"pid": pid}

    async def close_application(arguments: dict[str, object]) -> object:
        pid = _require_int(arguments, "pid")
        force = bool(arguments.get("force", False))
        await process.close_application(pid, force=force)
        return {"status": "closed", "pid": pid}

    async def clipboard_read(arguments: dict[str, object]) -> object:
        return {"text": await clipboard.read()}

    async def clipboard_write(arguments: dict[str, object]) -> object:
        text = _require_str(arguments, "text")
        await clipboard.write(text)
        return {"status": "written"}

    async def send_notification(arguments: dict[str, object]) -> object:
        title = _require_str(arguments, "title")
        message = _require_str(arguments, "message")
        await notifications.send(title=title, message=message)
        return {"status": "sent"}

    async def mouse_move(arguments: dict[str, object]) -> object:
        x = _require_int(arguments, "x")
        y = _require_int(arguments, "y")
        await input_service.move_mouse(x, y)
        return {"status": "moved", "x": x, "y": y}

    async def mouse_click(arguments: dict[str, object]) -> object:
        await input_service.click()
        return {"status": "clicked"}

    async def type_text(arguments: dict[str, object]) -> object:
        text = _require_str(arguments, "text")
        await input_service.type_text(text)
        return {"status": "typed"}

    async def press_key(arguments: dict[str, object]) -> object:
        key = _require_str(arguments, "key")
        await input_service.press_key(key)
        return {"status": "pressed", "key": key}

    registry.register(
        ToolSpec(
            name="list_processes",
            description="List running OS processes (pid, name, status).",
            risk_level=RiskLevel.SAFE,
            handler=list_processes,
            input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="open_application",
            description="Launch an application or command.",
            risk_level=RiskLevel.DANGEROUS,
            handler=open_application,
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": 'Argv, e.g. ["firefox"]',
                    }
                },
                "required": ["command"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="close_application",
            description="Terminate (or force-kill) a running process by pid.",
            risk_level=RiskLevel.DANGEROUS,
            handler=close_application,
            input_schema={
                "type": "object",
                "properties": {
                    "pid": {"type": "integer"},
                    "force": {"type": "boolean", "description": "Kill instead of terminate"},
                },
                "required": ["pid"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="clipboard_read",
            description="Read the current OS clipboard contents.",
            risk_level=RiskLevel.SENSITIVE,
            handler=clipboard_read,
            input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="clipboard_write",
            description="Write text to the OS clipboard.",
            risk_level=RiskLevel.SENSITIVE,
            handler=clipboard_write,
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="send_notification",
            description="Send a desktop notification.",
            risk_level=RiskLevel.SAFE,
            handler=send_notification,
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["title", "message"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="mouse_move",
            description="Move the mouse cursor to absolute screen coordinates.",
            risk_level=RiskLevel.SENSITIVE,
            handler=mouse_move,
            input_schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
                "required": ["x", "y"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="mouse_click",
            description="Click at the current mouse position.",
            risk_level=RiskLevel.DANGEROUS,
            handler=mouse_click,
            input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="type_text",
            description="Type text at the current input focus.",
            risk_level=RiskLevel.DANGEROUS,
            handler=type_text,
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="press_key",
            description="Press a single key (e.g. 'enter', 'esc').",
            risk_level=RiskLevel.DANGEROUS,
            handler=press_key,
            input_schema={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        )
    )
