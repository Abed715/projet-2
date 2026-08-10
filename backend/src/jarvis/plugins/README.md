# jarvis.plugins

**Status:** implemented (Phase 6). Depends on `jarvis.core`, `jarvis.brain`
(plugin tools register into a `ToolRegistry`), and `jarvis.security`
(risk levels, transitively — via the same `ToolRegistry`/`PermissionEngine`
path every other module's tools already go through).

## Public interface

```python
from jarvis.plugins import Plugin, PluginManifest, PluginLoader, GitHubPlugin
```

- **`PluginManifest(name, version, description, author="unknown")`** —
  purely declarative metadata: what a plugin is, for discovery/display.
  Loading a plugin never reads it to grant extra trust — see Design notes.
- **`Plugin`** — `Protocol`: a `manifest` property plus `register_tools(
  registry: ToolRegistry) -> None`. Any object with that shape is a
  plugin; there's no base class to inherit from.
- **`PluginLoader`** — `register(plugin)` adds a `Plugin` (raises
  `ConfigurationError` on a duplicate name), `load_all(registry)` calls
  every registered plugin's `register_tools(registry)` once and returns
  the manifests loaded, `list_plugins()` lists what's registered without
  loading anything.
- **`GitHubPlugin(client: httpx.AsyncClient)`** — the one reference plugin
  from ARCHITECTURE.md's Phase 6 scope. Registers a single tool,
  `github_repo_info(owner, repo)` (`SAFE` — public, read-only GitHub REST
  API), returning stars/forks/open issues/description/URL. `client` is
  injected the same way `web.WebAgent` takes its `httpx.AsyncClient`, so
  tests run against `httpx.MockTransport` with no real network calls.

## Design notes

- **Why there's no separate plugin sandbox, permission layer, or process
  boundary:** a plugin's *only* way to do anything is `register_tools`
  adding `ToolSpec`s to the caller's `ToolRegistry` — the same registry
  `system`/`web`/`automation`/`vision` register into. Every plugin tool
  call already goes through `PermissionEngine` (risk-based allow/confirm/
  deny by role), `AuditLog` (every invocation recorded, credential-looking
  params redacted), and whatever risk level the plugin declared on its
  `ToolSpec` — identical to a built-in module's tools. Building a second,
  plugin-specific security layer on top would duplicate a mechanism that
  already covers the actual requirement ("run through the full permission/
  sandbox path," per ARCHITECTURE.md's Phase 6 scope) rather than add
  anything a plugin could otherwise bypass.
- **Why `PluginManifest` doesn't drive permission decisions:** it's
  metadata for humans (a plugin manager UI listing name/version/author,
  per ARCHITECTURE.md's Phase 7 frontend scope), not a capability
  declaration the loader enforces. The actual capability boundary is each
  registered `ToolSpec`'s `risk_level` — checked at *invocation* time by
  `PermissionEngine`, the same as any other tool, regardless of which
  module or plugin registered it.
- **Why `GitHubPlugin` takes an already-constructed `httpx.AsyncClient`
  instead of building one itself:** same reasoning as `WebAgent` and every
  provider adapter in this codebase — constructing the client is
  production wiring, not something the plugin class should own, and it's
  what makes `httpx.MockTransport`-based testing possible with zero real
  network calls.
- **No plugin discovery/hot-loading from disk yet:** `PluginLoader.register`
  takes an already-instantiated `Plugin` object; there's no manifest-file-
  on-disk scanning, dynamic import, or install/uninstall flow yet. Those
  are real Phase 7 (frontend plugin manager) concerns — this phase ships
  the mechanism (`Plugin` protocol + loader + one working reference
  plugin), not a plugin marketplace.

## Known limitations / deferred

- `GitHubPlugin` is read-only and unauthenticated (public repos only, no
  GitHub token, no issues/PRs/write operations, no rate-limit-aware
  retry — a `503`/non-2xx response is surfaced as `ConfigurationError`
  as-is). A fuller GitHub integration is a real feature addition, not a
  fix to this reference implementation's scope.
- No plugin versioning/compatibility checks, no plugin-to-plugin
  dependencies, no per-plugin config schema — `PluginManifest` is
  intentionally minimal until a second real plugin's needs justify more.
- No `jarvis.api` surface for listing/enabling/disabling plugins at
  runtime yet (Phase 7 frontend concern, per ARCHITECTURE.md).
