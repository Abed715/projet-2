"""Research Agent: web search, doc reading, summarization — built on
`jarvis.web`'s tools via `ToolRunner`. See ARCHITECTURE.md §7.
"""

from __future__ import annotations

from typing import Any

from jarvis.agents.tool_agent import ToolAgent
from jarvis.brain.tool_runner import ToolRunner
from jarvis.brain.tools import ToolRegistry
from jarvis.security import Role

ALLOWED_TOOLS = frozenset({"web_search", "web_fetch"})

SYSTEM_PROMPT = (
    "You are the Research agent for JARVIS. Use web_search and web_fetch "
    "to find and read information, then answer the user's question or "
    "compare/summarize what you found. Cite the URLs you used. Only use "
    "the tools available to you — you cannot read local files or run "
    "commands."
)


def create_research_agent(
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
    return ToolAgent(name="research", system_prompt=SYSTEM_PROMPT, runner=runner, role=role)
