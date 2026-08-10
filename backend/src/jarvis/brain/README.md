# jarvis.brain

**Status:** implemented (Phase 2 chat path + Phase 3 tool-use loop). Depends
on `jarvis.core`, `jarvis.security`, and `jarvis.memory` (short-term).

## Public interface

```python
from jarvis.brain import (
    LLMProvider, Message, CompletionResult,   # provider protocol
    ClaudeProvider,                            # Claude (Anthropic) adapter
    LLMRouter,                                 # named provider registry
    ToolRegistry, ToolSpec, ToolInvocationResult, ToolInvocationStatus,
    ToolRunner, ToolRunResult,                 # agentic tool-use loop
    ConversationEngine,
)
```

- **`LLMProvider`** — the one interface every backend satisfies:
  `complete(messages, *, system=None) -> CompletionResult`. `Message.role`
  is `"user"`/`"assistant"` only — the system prompt is a separate
  argument, matching how the underlying provider APIs separate the two.
- **`ClaudeProvider`** — adapter over `anthropic.AsyncAnthropic`. Non-streaming
  `messages.create`, sufficient for the short conversational replies
  Coordinator/Planner/Reasoning need; streaming lands when a real workload
  needs it. Its `client` constructor argument is typed `Any` rather than
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
  on `ALLOW`. `system` and `web` (Phase 3) are the first modules to register
  real tools here; `automation`/`vision` (Phase 4) follow the same pattern.
- **`ToolRunner`** — the agentic loop for tool-using agents (Research,
  Coding): sends `messages.create` with a `tools` list built from
  `ToolRegistry.list_tools()` (optionally narrowed by `allowed_tools`, so
  an agent only ever sees its own subset), executes every `tool_use` block
  through `ToolRegistry.invoke` (permission + audit on every call), and
  feeds `tool_result`s back until Claude stops asking for tools. A
  `DANGEROUS` tool awaiting confirmation stops the loop immediately
  (`ToolRunResult.pending_confirmation`) rather than guessing — resuming
  after the user grants confirmation is a later phase's concern (the task
  engine, Phase 6). This is a **hand-written loop, not the SDK's beta tool
  runner** — JARVIS's confirmation semantics aren't something a generic
  runner knows about; see `shared/tool-use-concepts.md`'s manual-loop
  guidance.
- **`ConversationEngine`** — the plain-chat orchestration
  Coordinator/Planner/Reasoning use: appends the user turn to
  `ShortTermMemory`, assembles history into `Message`s, calls the
  router-selected provider with a given system prompt, appends the
  assistant turn, returns the reply text. Deliberately separate from
  `ToolRunner` — plain chat has no tool_use content blocks to round-trip,
  so mixing the two would complicate both.

## Design notes

- Two distinct agent shapes now exist: plain-chat agents (`agents.base.Agent`
  over `ConversationEngine`, Phase 2) and tool-using agents
  (`agents.tool_agent.ToolAgent` over `ToolRunner`, Phase 3). They don't
  share message history representations — `ConversationEngine` persists
  `ShortTermMemory` turns across calls; `ToolRunner` builds a fresh
  in-memory message list per `run()` call. Unifying them (so a tool-using
  agent also remembers prior turns across separate `run()` calls) is
  deferred until an agent actually needs both — likely when Coordinator
  gains delegation.
- Once domain tools exist, agents will also carry a tool subset — the
  `ToolRegistry` seam plus `ToolRunner.allowed_tools` are exactly that.
