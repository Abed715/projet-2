"""A tool-using agent: system prompt + a bounded tool subset, driven by
`ToolRunner` instead of `ConversationEngine` — Phase 2's plain-chat agents
(`agents.base.Agent`) have no tool access. Research and Coding are built on
this; Coordinator/Planner/Reasoning stay on the simpler chat path until
they have something to delegate to.
"""

from __future__ import annotations

from dataclasses import dataclass

from jarvis.brain.tool_runner import ToolRunner
from jarvis.security import Role


@dataclass(frozen=True, slots=True)
class ToolAgentReply:
    content: str
    pending_confirmation: str | None = None


class ToolAgent:
    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        runner: ToolRunner,
        role: Role = Role.OPERATOR,
    ) -> None:
        self.name = name
        self._system_prompt = system_prompt
        self._runner = runner
        self._role = role

    async def respond(
        self,
        session_id: str,
        user_message: str,
        *,
        actor: str | None = None,
        correlation_id: str | None = None,
    ) -> ToolAgentReply:
        result = await self._runner.run(
            system_prompt=self._system_prompt,
            user_message=user_message,
            role=self._role,
            session_id=session_id,
            actor=actor or self.name,
            correlation_id=correlation_id or session_id,
        )
        return ToolAgentReply(
            content=result.final_text, pending_confirmation=result.pending_confirmation
        )
