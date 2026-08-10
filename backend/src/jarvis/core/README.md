# jarvis.core

**Status:** implemented (Phase 0).

Foundation module every other package depends on. Contains no business logic
of its own — only the primitives the rest of the system is built from.

## Public interface

```python
from jarvis.core import (
    Settings, get_settings,          # environment-driven configuration
    configure_logging, get_logger,   # structured logging
    JarvisError, ConfigurationError, NotFoundError,
    PermissionDeniedError, ValidationError,   # exception hierarchy
    Container,                       # minimal dependency-injection container
    EventBus, Event, InMemoryEventBus,        # internal pub/sub interface
)
```

- **`Settings`** — a `pydantic-settings` `BaseSettings` subclass. Reads from
  environment variables / `.env` (see `.env.example` at repo root). Access
  via `get_settings()`, which is `lru_cache`-memoized — call it, don't
  construct `Settings()` directly, so the whole process shares one instance.
- **`configure_logging` / `get_logger`** — stdlib `logging` configured for
  structured (JSON in production, human-readable in development) output with
  a `correlation_id` field threaded through via `contextvars`, so a whole
  request/task can be traced across modules.
- **Exceptions** — `JarvisError` is the base class every module-specific
  exception should inherit from, so the API layer can map errors to HTTP
  responses in one place.
- **`Container`** — a small explicit-registration DI container (no magic
  autowiring). Modules register factories; `api` composes the app from it.
- **`EventBus`** — the `Protocol` other modules use to publish/subscribe to
  internal events (e.g. `MemoryCandidate`, permission decisions). Phase 0
  ships an in-memory implementation sufficient for a single-process
  deployment; a Redis-backed implementation lands in Phase 1 alongside
  `memory`/`security` without changing the interface.

## Design notes

- No module below `core` in the dependency graph may import from `security`
  or any domain module (see `ARCHITECTURE.md §5.1`).
- Settings are validated at startup (`get_settings()` raising is a fatal
  boot error, by design) rather than failing lazily deep in a request.
