"""Automation Agent: process/clipboard/notification/input control via
`jarvis.automation`'s tools through `ToolRunner`. See ARCHITECTURE.md §7.
"""

from __future__ import annotations

from typing import Any

from jarvis.agents.tool_agent import ToolAgent
from jarvis.brain.tool_runner import ToolRunner
from jarvis.brain.tools import ToolRegistry
from jarvis.security import Role

ALLOWED_TOOLS = frozenset(
    {
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
)

SYSTEM_PROMPT = (
    "You are the Automation agent for JARVIS. You can list, launch, and "
    "close applications, read and write the clipboard, send desktop "
    "notifications, and control the mouse and keyboard. Explain what "
    "you're about to do before doing it. Launching/closing applications "
    "and any mouse/keyboard action will pause for user confirmation — if "
    "that happens, stop and report what you were about to do instead of "
    "retrying."
)


def create_automation_agent(
    client: Any,
    registry: ToolRegistry,
    *,
    role: Role = Role.OPERATOR,
    model: str | None = None,
) -> ToolAgent:
    runner_kwargs: dict[str, Any] = {"registry": registry, "allowed_tools": ALLOWED_TOOLS}
    if model is not None:
        runner_kwargs["model"] = model
    runner = ToolRunner(client, **runner_kwargs)
    return ToolAgent(name="automation", system_prompt=SYSTEM_PROMPT, runner=runner, role=role)
