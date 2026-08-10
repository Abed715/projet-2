"""Conversation orchestration shared by all agents: assembles history from
short-term memory, calls the selected LLM provider, and records the new
turns. Concrete agents (`jarvis.agents` — Coordinator, Planner, Reasoning)
are thin wrappers over this with a fixed system prompt and provider name.
"""

from __future__ import annotations

from jarvis.brain.providers.base import Message
from jarvis.brain.router import LLMRouter
from jarvis.memory.short_term import ShortTermMemory, Turn


class ConversationEngine:
    def __init__(self, *, memory: ShortTermMemory, router: LLMRouter) -> None:
        self._memory = memory
        self._router = router

    async def respond(
        self,
        session_id: str,
        user_message: str,
        *,
        system_prompt: str,
        provider_name: str,
    ) -> str:
        await self._memory.append(session_id, Turn(role="user", content=user_message))

        history = await self._memory.get_turns(session_id)
        messages = [Message(role=turn.role, content=turn.content) for turn in history]

        provider = self._router.get(provider_name)
        result = await provider.complete(messages, system=system_prompt)

        await self._memory.append(session_id, Turn(role="assistant", content=result.content))
        return result.content
