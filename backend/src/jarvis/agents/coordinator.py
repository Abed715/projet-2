"""Coordinator: the entry point for a user turn. Phase 2 ships it as a
plain conversational agent — deciding direct-answer vs. delegate-to-Planner
and merging sub-agent results (ARCHITECTURE.md §7) lands once Planner and
domain agents exist to delegate to.
"""

from __future__ import annotations

from jarvis.agents.base import Agent
from jarvis.brain.conversation import ConversationEngine

SYSTEM_PROMPT = (
    "You are JARVIS, a helpful AI assistant. Respond directly and concisely. "
    "You do not yet have access to tools, long-term memory search, or "
    "sub-agents — those capabilities are added in later development phases; "
    "do not claim to have them."
)


def create_coordinator(engine: ConversationEngine, *, provider_name: str = "anthropic") -> Agent:
    return Agent(
        name="coordinator",
        system_prompt=SYSTEM_PROMPT,
        engine=engine,
        provider_name=provider_name,
    )
