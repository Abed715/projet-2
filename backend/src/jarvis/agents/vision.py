"""Vision Agent: screen/image understanding via `jarvis.vision`'s tools
through `ToolRunner`. See ARCHITECTURE.md §7.
"""

from __future__ import annotations

from typing import Any

from jarvis.agents.tool_agent import ToolAgent
from jarvis.brain.tool_runner import ToolRunner
from jarvis.brain.tools import ToolRegistry
from jarvis.security import Role

ALLOWED_TOOLS = frozenset({"extract_text", "analyze_image", "capture_screen", "list_windows"})

SYSTEM_PROMPT = (
    "You are the Vision agent for JARVIS. You can take a screenshot, list "
    "open windows, run OCR on an image, and get basic image metadata "
    "(size, format, average color). Use these to describe what's on "
    "screen or read text out of an image. You cannot control the mouse "
    "or keyboard, or detect objects/scenes — only read what's already "
    "visible."
)


def create_vision_agent(
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
    return ToolAgent(name="vision", system_prompt=SYSTEM_PROMPT, runner=runner, role=role)
