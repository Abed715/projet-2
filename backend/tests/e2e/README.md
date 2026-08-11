# tests/e2e

**Status:** implemented (Phase 8). Out-of-process, full-stack tests — the
third tier alongside `tests/unit` (fast, no real I/O) and
`tests/integration` (real Postgres/Redis, in-process). Excluded from the
default `pytest` run (`testpaths` in `pyproject.toml` only lists
`tests/unit`/`tests/integration`) because each test costs real subprocess
startup time; run it explicitly:

```bash
pytest tests/e2e -m e2e -v
# or
make e2e
```

CI runs it as its own job (`e2e` in `backend-ci.yml`), separate from the
fast unit/integration job.

## What "e2e" means here

Every other test tier in this repo — deliberately — never makes a real
network call and never imports the app as anything other than a Python
object (`TestClient(create_app())`, `ToolRegistry` fixtures, fake
providers). That's correct for testing business logic, but it never
proves the actual deployable artifact — a real `uvicorn` process, bound to
a real socket, talking to a real Redis over a real TCP connection — works.
This tier does:

- **`redis_port`** (session-scoped fixture) — starts a real `redis-server`
  subprocess on an ephemeral port. Self-contained: no dependency on a
  pre-existing service container, works identically locally and in CI.
- **`fake_anthropic_server`** — a real HTTP server (stdlib
  `http.server.ThreadingHTTPServer`) implementing just enough of
  Anthropic's Messages API shape (`POST /v1/messages` → a canned
  response) to stand in for `https://api.anthropic.com`. Records every
  request body it receives so tests can assert on what the real backend
  process actually sent.
- **`backend_base_url`** — launches `uvicorn jarvis.api.app:create_app
  --factory` as a real subprocess (the exact command
  `infra/docker/backend.Dockerfile` runs), pointed at `redis_port` and
  `fake_anthropic_server` via real environment variables
  (`REDIS_HOST`/`REDIS_PORT`, `ANTHROPIC_API_KEY`/`ANTHROPIC_BASE_URL` —
  `anthropic_base_url` is a `Settings` field added specifically to make
  this possible, see `core/settings.py`). Polls `/health` until the
  process is actually ready, and captures stdout/stderr for a useful
  failure message if it never comes up.

What this proves that no other test tier does: the real ASGI server boots
from real environment variables, the real WebSocket handshake and framing
work over a real socket, `ConversationEngine` persists and reloads session
history through a **real** Redis (not `fakeredis`), and the Anthropic
SDK's real HTTP client successfully makes and parses a real HTTP
request/response — all without a real Anthropic API key or a real network
call to Anthropic, which the whole rest of this repo's testing philosophy
rules out.

## What's here

- `test_health.py` — `GET /health` and the correlation-ID header, against
  a real running server.
- `test_chat_round_trip.py` — the main test: two turns over a real `WS
  /ws/chat` connection, asserting both the replies and that the *second*
  LLM call's message history includes the first turn — proof that session
  state actually round-tripped through real Redis, not just that the
  first message worked.
- `test_voice_not_configured.py` — `WS /ws/voice`'s "not configured" close
  path (code `1011`, reason `"voice not configured"`) over a real socket.

## Known limitations / deferred

- No Postgres in these fixtures — nothing on the `/ws/chat` or `/health`
  path touches it (`EpisodicStore`/`Database` aren't constructed by
  `create_app()`). If a future e2e test needs it, add a `postgres_port`
  fixture following the same "spawn our own, ephemeral, self-contained"
  pattern as `redis_port`.
- No e2e coverage yet for `/ws/voice`'s actual audio path (only the
  "not configured" close), or for tool-using agents (Research/Coding/
  Automation/Vision) — those aren't reachable from `jarvis.api` yet (see
  `agents/README.md`), so there's no HTTP/WS surface to e2e-test against.
- No e2e coverage of the frontend/desktop clients against a real backend
  — that was verified manually with Playwright during Phase 7 (see the
  session notes) but isn't automated here; a `frontend/e2e` Playwright
  suite is a reasonable next addition if this project keeps growing.
