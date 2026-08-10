"""Coding Agent: repo-scoped read/modify/debug via `jarvis.system`'s tools
through `ToolRunner`. See ARCHITECTURE.md §7.

"Repo-scoped" means confined to the workspace directory `FilesystemService`
and `ShellService` are constructed against — there's no separate repo
sandbox here, `system`'s existing workspace confinement is what scopes it.
"""

from __future__ import annotations

from typing import Any

from jarvis.agents.tool_agent import ToolAgent
from jarvis.brain.tool_runner import ToolRunner
from jarvis.brain.tools import ToolRegistry
from jarvis.security import Role

ALLOWED_TOOLS = frozenset(
    {"read_file", "list_dir", "write_file", "move_file", "delete_file", "run_shell_command"}
)

SYSTEM_PROMPT = (
    "You are the Coding agent for JARVIS. You can read, write, move, and "
    "delete files, and run shell commands, all confined to the current "
    "workspace. Explain what you changed and why. Destructive actions "
    "(deleting files, running shell commands) will pause for user "
    "confirmation — if that happens, stop and report what you were about "
    "to do instead of retrying."
)


def create_coding_agent(
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
    return ToolAgent(name="coding", system_prompt=SYSTEM_PROMPT, runner=runner, role=role)
