# jarvis.api

**Status:** implemented through Phase 5 — health check, streaming chat,
voice turns.

The composition root: the only module allowed to depend on every other
module, and the only place HTTP/WebSocket concerns live. Contains no
business logic itself.

## Current surface

- `create_app(*, coordinator: Agent | None = None, voice_pipeline:
  VoicePipeline | None = None)` — FastAPI application factory. Wires
  `core` settings and logging, installs a correlation-ID middleware,
  registers the exception handler that maps `JarvisError` subclasses to
  HTTP responses, and mounts routers.
  - `coordinator` is a dependency-injection seam: omitted in production
    (the default builds a real `ClaudeProvider` + Redis-backed short-term
    memory from process settings), overridden with a fake `Agent` in
    tests so `/ws/chat` is exercised with no network calls and no live
    Redis.
  - `voice_pipeline` is the same seam for `/ws/voice`: omitted in
    production to lazily build the real Whisper/Piper-backed
    `voice.VoicePipeline` on the *first* `/ws/voice` connection (not at
    `create_app()` time — see `_build_default_voice_pipeline`'s
    docstring for why loading real STT/TTS models can't be eager like
    the coordinator's lazy client handles), overridden with a fake in
    tests.
- `GET /health` — liveness check; returns `{"status": "ok"}`.
- `WS /ws/chat` — one WebSocket connection is one conversation session
  (a fresh UUID per connection, reused across messages on that connection).
  Send plain text, receive the Coordinator agent's plain-text reply.
  Framing, streaming token-by-token, and auth land alongside multi-user
  support in later phases — this is intentionally the simplest possible
  wire format to prove the stack end to end.
- `WS /ws/voice` — one connection is one voice session, same session-per-
  connection model as `/ws/chat`. Send binary audio bytes (one message per
  utterance), receive synthesized reply audio bytes. If
  `JARVIS_PIPER_VOICE_MODEL_PATH` isn't configured, the connection is
  accepted and then closed immediately with code `1011` and reason
  `"voice not configured"` — a clear, non-crashing failure mode rather
  than a silent hang or a 500. Non-streaming (whole utterance in, whole
  reply out), matching how `/ws/chat` started in Phase 2; see
  `voice/README.md` for what's deferred (streaming, VAD, barge-in,
  continuous wake-word listening).

## Planned surface (later phases)

- `POST /api/v1/...` REST routers per domain module, added as those modules
  ship.

Run locally: `uvicorn jarvis.api.app:create_app --factory --reload`.
