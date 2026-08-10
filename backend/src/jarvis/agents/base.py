"""Thin per-agent wrapper over `brain`'s shared conversation engine: a
system prompt and a provider name, nothing else. See ARCHITECTURE.md §7 —
agents differ only in system prompt and (once domain tools exist) which
tools they can see.
"""

from __future__ import annotations

from dataclasses import dataclass

from jarvis.brain.conversation import ConversationEngine


@dataclass(frozen=True, slots=True)
class AgentReply:
    content: str


class Agent:
    """A named system prompt driving `ConversationEngine` for one provider."""

    def __init__(
        self, *, name: str, system_prompt: str, engine: ConversationEngine, provider_name: str
    ) -> None:
        self.name = name
        self._system_prompt = system_prompt
        self._engine = engine
        self._provider_name = provider_name

    async def respond(self, session_id: str, user_message: str) -> AgentReply:
        content = await self._engine.respond(
            session_id,
            user_message,
            system_prompt=self._system_prompt,
            provider_name=self._provider_name,
        )
        return AgentReply(content=content)
