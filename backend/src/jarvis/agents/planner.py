"""Planner: turns a goal into an ordered plan. Phase 2 ships it as a plain
conversational agent that reasons about plans in text; producing structured
tool-call plans over the tool registry (ARCHITECTURE.md §7) lands once
domain modules register tools worth planning over.
"""

from __future__ import annotations

from jarvis.agents.base import Agent
from jarvis.brain.conversation import ConversationEngine

SYSTEM_PROMPT = (
    "You are the Planning agent for JARVIS. Given a goal, break it into a "
    "clear, ordered list of concrete steps. You do not execute steps "
    "yourself — you only produce the plan for another agent to carry out."
)


def create_planner(engine: ConversationEngine, *, provider_name: str = "anthropic") -> Agent:
    return Agent(
        name="planner", system_prompt=SYSTEM_PROMPT, engine=engine, provider_name=provider_name
    )
