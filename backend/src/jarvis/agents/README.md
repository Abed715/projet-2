# jarvis.agents

**Status:** implemented (Phase 2 chat agents + Phase 3/4 tool-using agents).
Depends on `jarvis.brain`, and on `jarvis.web`/`jarvis.system`/
`jarvis.automation`/`jarvis.vision` for what the tool-using agents' tools
do (those modules register the tools into the `ToolRegistry` an agent's
caller passes in — this module doesn't import them itself).

## Public interface

```python
from jarvis.agents import (
    Agent, AgentReply,                         # plain-chat agent wrapper
    ToolAgent, ToolAgentReply,                  # tool-using agent wrapper
    create_coordinator, create_planner, create_reasoning_agent,   # chat agents
    create_research_agent, create_coding_agent,                   # tool-using agents
    create_automation_agent, create_vision_agent,                 # tool-using agents
)
```

- **`Agent`** — a name, a system prompt, and a provider name over
  `brain.ConversationEngine`. Coordinator, Planner, and Reasoning are built
  on this; none of them call tools.
- **`ToolAgent`** — a name, a system prompt, a role, and a `ToolRunner`.
  Research and Coding are built on this; `respond()` drives one full
  tool-use loop and returns the final text (or which tool is pending
  confirmation, if the loop stopped for that reason — see
  `brain/tool_runner.py`).
- **`create_coordinator`** — entry point for a user turn. Currently a plain
  conversational agent; deciding direct-answer vs. delegate-to-Planner/
  Research/Coding and merging results lands once Coordinator itself needs
  to call tools (a `ToolAgent`, at that point).
- **`create_planner`** — turns a goal into an ordered list of steps, in
  text. Producing a structured plan over `brain.ToolRegistry` lands once
  Planner needs to inspect what tools are actually available.
- **`create_reasoning_agent`** — general chain-of-thought reasoning not
  tied to a specific domain.
- **`create_research_agent`** — web search, doc reading, summarization.
  Scoped to `web_search`/`web_fetch` only (`agents.research.ALLOWED_TOOLS`)
  — it cannot read local files or run commands, even if a caller registers
  those tools on the same `ToolRegistry` instance.
- **`create_coding_agent`** — repo-scoped read/modify/debug. Scoped to
  `system`'s file and shell tools (`agents.coding.ALLOWED_TOOLS`).
  "Repo-scoped" means confined to the workspace directory `system`'s
  services were constructed against, not a separate sandbox this module
  adds.
- **`create_automation_agent`** — process/clipboard/notification/input
  control. Scoped to `automation`'s tools (`agents.automation.ALLOWED_TOOLS`)
  — it cannot read files, run shell commands, or use `web`/`vision` tools.
- **`create_vision_agent`** — screen/image understanding: screenshots,
  window listing, OCR, basic image metadata. Scoped to `vision`'s tools
  (`agents.vision.ALLOWED_TOOLS`). Read-only by design — it cannot control
  the mouse/keyboard (that's `automation`'s job) or detect objects/scenes
  (not implemented in `vision` yet).

Chat-agent factories take a `ConversationEngine` and an optional
`provider_name` (defaults to `"anthropic"`). Tool-agent factories take the
raw provider client (the same one `ClaudeProvider` wraps — `ToolRunner`
talks to `messages.create` directly, see `brain/tool_runner.py`) and a
`ToolRegistry`, plus an optional `role` (defaults to `Role.OPERATOR`) and
`model`.

## Design notes

- Adding a chat agent is configuration (a new system prompt + factory
  function); adding a tool-using agent is a system prompt + an
  `ALLOWED_TOOLS` set — both match the "agents are cheap" principle in
  ARCHITECTURE.md §2.4.
- **Why two wrapper classes (`Agent` vs. `ToolAgent`) instead of one:**
  `ConversationEngine` persists plain-text turns to `ShortTermMemory` across
  calls; `ToolRunner` builds a fresh in-memory message list (including
  structured `tool_use`/`tool_result` content blocks) per `run()` call and
  doesn't persist anything. Forcing them through one shape would either
  strip tool support from chat agents or bolt persistent memory onto every
  tool call — neither is needed yet. Unifying them is deferred until an
  agent actually needs both (multi-turn memory *and* tools) — likely when
  Coordinator gains delegation.
- Memory and Security agents (ARCHITECTURE.md §7) are deferred until there's
  a concrete consumer for a memory-specific or security-specific agent —
  unlike Automation/Vision, neither wraps a domain module that didn't exist
  yet, so there's no phase forcing the question.
