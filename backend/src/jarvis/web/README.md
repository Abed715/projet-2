# jarvis.web

**Status:** implemented (Phase 3). Depends on `jarvis.core` and
`jarvis.brain` (to register tools into `ToolRegistry`).

## Public interface

```python
from jarvis.web import (
    parse_html, ParsedPage,                          # dependency-free HTML extraction
    WebAgent, FetchedPage, create_http_client,        # fetch
    SearchProvider, SearchResult, DuckDuckGoSearchProvider,  # search
    register_web_tools,
)
```

- **`parse_html`** — a pure function (stdlib `html.parser` only, no extra
  dependency) that extracts a page's `<title>`, visible text, and any
  `<table>` contents. Used by `WebAgent.fetch`; also directly testable and
  usable on its own.
- **`WebAgent`** — `fetch(url) -> FetchedPage` (with a best-effort SSRF
  guard rejecting literal loopback/private-IP/`localhost` URLs — see the
  class docstring for what it can't catch) and `search(query) ->
  list[SearchResult]` (delegates to an injected `SearchProvider`).
  `create_http_client()` builds the `httpx.AsyncClient` used in production;
  tests inject a client built on `httpx.MockTransport` instead, so the
  suite makes no real network calls.
- **`SearchProvider`** — mirrors `brain.LLMProvider`'s pattern: one
  interface, swappable backends. `DuckDuckGoSearchProvider` is the only
  implementation today (no API key required); a paid provider (Bing,
  Brave, Serper, ...) can be swapped in later behind the same interface
  with no change to `WebAgent` or tool registration.
- **`register_web_tools(registry, *, web_agent)`** — registers `web_search`
  and `web_fetch` as `SENSITIVE` tools (logged, blocked for `GUEST`,
  allowed without confirmation for `OPERATOR`+ — outbound network access
  isn't destructive, but it is a real capability worth an audit trail).

## Design notes

- **Summarization and comparison are not this module's job.** `web` only
  provides raw material (fetched text, search snippets); the Research
  Agent (`jarvis.agents`) is what asks an LLM to summarize or compare —
  matching the split in ARCHITECTURE.md §3.1 between domain modules
  (tools) and agents (reasoning over tools).
- **`DuckDuckGoSearchProvider` is best-effort.** It scrapes DuckDuckGo's
  plain HTML results endpoint — there's no stable API contract, so a
  layout change upstream can break it. This is an accepted tradeoff for
  "search with no API key to provision"; production deployments that need
  reliability should swap in a paid `SearchProvider` implementation.
- The SSRF guard in `WebAgent.fetch` checks the URL's literal hostname
  against loopback/private/link-local/reserved IP ranges (and the string
  `"localhost"`) before the request. It's a best-effort mitigation, not a
  complete one: a domain that resolves to a private address only at
  request time (DNS rebinding) isn't caught here — that requires
  network-level egress control this module doesn't own.
