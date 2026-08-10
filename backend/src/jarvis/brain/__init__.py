"""jarvis.brain — LLM provider router, tool registry, conversation
orchestration shared by all agents.

See README.md for the full public interface and design notes.
"""

from jarvis.brain.conversation import ConversationEngine
from jarvis.brain.providers import ClaudeProvider, CompletionResult, LLMProvider, Message
from jarvis.brain.router import LLMRouter
from jarvis.brain.tools import (
    ToolHandler,
    ToolInvocationResult,
    ToolInvocationStatus,
    ToolRegistry,
    ToolSpec,
)

__all__ = [
    "ConversationEngine",
    "ClaudeProvider",
    "CompletionResult",
    "LLMProvider",
    "Message",
    "LLMRouter",
    "ToolHandler",
    "ToolInvocationResult",
    "ToolInvocationStatus",
    "ToolRegistry",
    "ToolSpec",
]
