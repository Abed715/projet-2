"""Reasoning agent: general multi-step reasoning not tied to a specific
domain tool. See ARCHITECTURE.md §7.
"""

from __future__ import annotations

from jarvis.agents.base import Agent
from jarvis.brain.conversation import ConversationEngine

SYSTEM_PROMPT = (
    "You are the Reasoning agent for JARVIS. Think step by step through the "
    "problem presented and give a clear, well-justified answer, stating any "
    "assumptions you make along the way."
)


def create_reasoning_agent(
    engine: ConversationEngine, *, provider_name: str = "anthropic"
) -> Agent:
    return Agent(
        name="reasoning", system_prompt=SYSTEM_PROMPT, engine=engine, provider_name=provider_name
    )
