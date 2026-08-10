# jarvis.brain

**Status:** implemented (Phase 2) — LLM router with the Claude adapter,
tool registry, conversation orchestration. Depends on `jarvis.core`,
`jarvis.security`, and `jarvis.memory` (short-term).

## Public interface

```python
from jarvis.brain import (
    LLMProvider, Message, CompletionResult,   # provider protocol
    ClaudeProvider,                            # Claude (Anthropic) adapter
    LLMRouter,                                 # named provider registry
    ToolRegistry, ToolSpec, ToolInvocationResult, ToolInvocationStatus,
    ConversationEngine,
)
```

- **`LLMProvider`** — the one interface every backend satisfies:
  `complete(messages, *, system=None) -> CompletionResult`. `Message.role`
  is `"user"`/`"assistant"` only — the system prompt is a separate
  argument, matching how the underlying provider APIs separate the two.
- **`ClaudeProvider`** — adapter over `anthropic.AsyncAnthropic`. Non-streaming
  `messages.create`, sufficient for the short conversational replies this
  phase needs; streaming and tool-use round-trips land when a real workload
  needs them. Its `client` constructor argument is typed `Any` rather than
  the real SDK class specifically so tests can inject a lightweight double
  (`messages.create(...)` only) — no real network calls in the test suite.
  OpenAI and Ollama adapters follow the same `LLMProvider` interface in a
  later phase (ARCHITECTURE.md §4).
- **`LLMRouter`** — a named registry (`"anthropic"` today); callers select a
  provider by name so swapping backends is configuration, not a code change.
- **`ToolRegistry`** — the enforcement seam for domain tools: `register()`
  ties a tool's risk level into `security.PermissionEngine`; `invoke()`
  evaluates the permission decision, writes an `AuditEntry` unconditionally
  (allow, deny, or requires-confirmation), then only calls the tool handler
  on `ALLOW`. No domain tools are registered yet — `system`/`web`/
  `automation`/`vision` (Phases 3-4) register real ones here; this module
  ships the plumbing first so those tools inherit the permission/audit path
  for free.
- **`ConversationEngine`** — the orchestration `jarvis.agents` builds on:
  appends the user turn to `ShortTermMemory`, assembles history into
  `Message`s, calls the router-selected provider with a given system
  prompt, appends the assistant turn, returns the reply text.

## Design notes

- Agents (Phase 2, `jarvis.agents`) are thin: a system prompt + a provider
  name over `ConversationEngine`. Once domain tools exist, agents will also
  carry a tool subset — the `ToolRegistry` seam is already here for that.
- `ConversationEngine` only touches short-term memory. Summarizing aging
  turns into durable episodic memory before they're trimmed is the Memory
  Agent's job (ARCHITECTURE.md §6), not this module's.
