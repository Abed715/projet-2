"""jarvis.agents — concrete agents built on brain's conversation engine and
tool-use loop.

See README.md for the full public interface and design notes.
"""

from jarvis.agents.automation import create_automation_agent
from jarvis.agents.base import Agent, AgentReply
from jarvis.agents.coding import create_coding_agent
from jarvis.agents.coordinator import create_coordinator
from jarvis.agents.planner import create_planner
from jarvis.agents.reasoning import create_reasoning_agent
from jarvis.agents.research import create_research_agent
from jarvis.agents.tool_agent import ToolAgent, ToolAgentReply
from jarvis.agents.vision import create_vision_agent

__all__ = [
    "Agent",
    "AgentReply",
    "ToolAgent",
    "ToolAgentReply",
    "create_coordinator",
    "create_planner",
    "create_reasoning_agent",
    "create_research_agent",
    "create_coding_agent",
    "create_automation_agent",
    "create_vision_agent",
]
