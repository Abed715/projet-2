# jarvis.agents

**Status:** implemented (Phase 2) — Coordinator, Planner, Reasoning agents.
Depends on `jarvis.brain` (and, once domain tools exist, the modules that
register them — not yet, in this phase).

## Public interface

```python
from jarvis.agents import (
    Agent, AgentReply,             # the thin wrapper every agent is built from
    create_coordinator,
    create_planner,
    create_reasoning_agent,
)
```

- **`Agent`** — a name, a system prompt, and a provider name over
  `brain.ConversationEngine`. This is the entire agent abstraction per
  ARCHITECTURE.md §7: "all agents are thin: a system prompt + a tool subset
  + an `LLMProvider` call." The tool subset is still empty in this phase —
  no domain tools exist yet — so every agent here is system-prompt-only.
- **`create_coordinator`** — entry point for a user turn. Currently a plain
  conversational agent; deciding direct-answer vs. delegate-to-Planner and
  merging results lands once there's something to delegate to.
- **`create_planner`** — turns a goal into an ordered list of steps, in
  text. Producing a structured plan over `brain.ToolRegistry` lands once
  domain tools exist to plan over.
- **`create_reasoning_agent`** — general chain-of-thought reasoning not
  tied to a specific domain.

Each factory takes a `ConversationEngine` and an optional `provider_name`
(defaults to `"anthropic"`, i.e. the `ClaudeProvider` registered in
`jarvis.api.app`).

## Design notes

- Adding an agent is configuration (a new system prompt + factory
  function), not a new execution engine — matches the "agents are cheap"
  principle in ARCHITECTURE.md §2.4.
- Research, Coding, Memory, Automation, Security, and Vision agents
  (ARCHITECTURE.md §7) are deferred until the domain modules they wrap
  (`web`, `system`, `automation`, `vision`) exist in Phases 3-4 — an agent
  with no tools to call and no memory to search would just be a copy of
  Reasoning with a different name.
