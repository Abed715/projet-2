# jarvis.api

**Status:** implemented through Phase 2 — health check + streaming chat.

The composition root: the only module allowed to depend on every other
module, and the only place HTTP/WebSocket concerns live. Contains no
business logic itself.

## Current surface

- `create_app(*, coordinator: Agent | None = None)` — FastAPI application
  factory. Wires `core` settings and logging, installs a correlation-ID
  middleware, registers the exception handler that maps `JarvisError`
  subclasses to HTTP responses, and mounts routers. The `coordinator`
  parameter is a dependency-injection seam: omitted in production (the
  default builds a real `ClaudeProvider` + Redis-backed short-term memory
  from process settings), overridden with a fake `Agent` in tests so
  `/ws/chat` is exercised with no network calls and no live Redis.
- `GET /health` — liveness check; returns `{"status": "ok"}`.
- `WS /ws/chat` — one WebSocket connection is one conversation session
  (a fresh UUID per connection, reused across messages on that connection).
  Send plain text, receive the Coordinator agent's plain-text reply.
  Framing, streaming token-by-token, and auth land alongside `jarvis.voice`
  and multi-user support in later phases — this is intentionally the
  simplest possible wire format to prove the stack end to end.

## Planned surface (later phases)

- `POST /api/v1/...` REST routers per domain module, added as those modules
  ship.
- `WS /ws/voice` — audio streaming endpoint (Phase 5).

Run locally: `uvicorn jarvis.api.app:create_app --factory --reload`.
