"""Manual agentic tool-use loop over Claude's Messages API, with every tool
call gated through `ToolRegistry` (permission + audit) before it runs.

A hand-written loop — rather than a generic SDK tool runner — is required
here: JARVIS's confirmation semantics (`RiskLevel`/`PermissionDecision`)
aren't something a generic tool runner knows about, and a `DANGEROUS` tool
awaiting confirmation must stop the loop instead of guessing. See
shared/tool-use-concepts.md's "manual agentic loop" guidance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from jarvis.brain.tools import ToolInvocationStatus, ToolRegistry
from jarvis.core.exceptions import ConfigurationError, PermissionDeniedError
from jarvis.security import Role

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_MAX_ITERATIONS = 10


@dataclass(frozen=True, slots=True)
class ToolRunResult:
    """The outcome of one `ToolRunner.run()` call.

    `pending_confirmation` is set (and `final_text` is empty) when the loop
    stopped because a `DANGEROUS` tool needs explicit user confirmation —
    resuming after that confirmation is granted is a later phase's concern
    (the task engine, Phase 6); this phase surfaces the stop cleanly rather
    than guessing or silently dropping the request.
    """

    final_text: str
    iterations: int
    pending_confirmation: str | None = None


class ToolRunner:
    """Drives one Claude conversation through `tool_use` round-trips.

    `client` is typed as `Any` for the same reason as `ClaudeProvider`
    (see brain/providers/claude.py) — tests inject a double exposing only
    `messages.create(...)`, no real network calls.
    """

    def __init__(
        self,
        client: Any,
        *,
        registry: ToolRegistry,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        allowed_tools: frozenset[str] | None = None,
    ) -> None:
        self._client = client
        self._registry = registry
        self._model = model
        self._max_tokens = max_tokens
        self._max_iterations = max_iterations
        self._allowed_tools = allowed_tools

    def _tool_definitions(self) -> list[dict[str, Any]]:
        tools = self._registry.list_tools()
        if self._allowed_tools is not None:
            tools = [tool for tool in tools if tool.name in self._allowed_tools]
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools
        ]

    async def run(
        self,
        *,
        system_prompt: str,
        user_message: str,
        role: Role,
        session_id: str,
        actor: str,
        correlation_id: str,
    ) -> ToolRunResult:
        tools = self._tool_definitions()
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]

        for iteration in range(1, self._max_iterations + 1):
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                return ToolRunResult(final_text=text, iterations=iteration)

            tool_results, pending_confirmation = await self._execute_tool_calls(
                response.content,
                role=role,
                session_id=session_id,
                actor=actor,
                correlation_id=correlation_id,
            )
            messages.append({"role": "user", "content": tool_results})

            if pending_confirmation is not None:
                return ToolRunResult(
                    final_text="", iterations=iteration, pending_confirmation=pending_confirmation
                )

        raise ConfigurationError(
            f"tool loop did not converge within {self._max_iterations} iterations"
        )

    async def _execute_tool_calls(
        self,
        content_blocks: list[Any],
        *,
        role: Role,
        session_id: str,
        actor: str,
        correlation_id: str,
    ) -> tuple[list[dict[str, Any]], str | None]:
        tool_results: list[dict[str, Any]] = []
        pending_confirmation: str | None = None

        for block in content_blocks:
            if block.type != "tool_use":
                continue

            if self._allowed_tools is not None and block.name not in self._allowed_tools:
                raise PermissionDeniedError(
                    f"tool {block.name!r} is not in this agent's allowed tool set"
                )

            result = await self._registry.invoke(
                name=block.name,
                arguments=dict(block.input),
                role=role,
                session_id=session_id,
                actor=actor,
                correlation_id=correlation_id,
            )

            if result.status is ToolInvocationStatus.REQUIRES_CONFIRMATION:
                pending_confirmation = block.name
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": (
                            f"{block.name} requires explicit user confirmation "
                            "before it can run."
                        ),
                        "is_error": True,
                    }
                )
                continue

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result.result),
                }
            )

        return tool_results, pending_confirmation
