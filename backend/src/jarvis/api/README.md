# jarvis.api

**Status:** minimal implementation (Phase 0) — health check only.

The composition root: the only module allowed to depend on every other
module, and the only place HTTP/WebSocket concerns live. Contains no
business logic itself.

## Current surface

- `create_app()` — FastAPI application factory. Wires `core` settings and
  logging, installs a correlation-ID middleware, registers the exception
  handler that maps `JarvisError` subclasses to HTTP responses, and mounts
  routers.
- `GET /health` — liveness check; returns `{"status": "ok"}`.

## Planned surface (later phases)

- `POST /api/v1/...` REST routers per domain module, added as those modules
  ship.
- `WS /ws/chat` — streaming conversation endpoint (Phase 2).
- `WS /ws/voice` — audio streaming endpoint (Phase 5).

Run locally: `uvicorn jarvis.api.app:create_app --factory --reload`.
