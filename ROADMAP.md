# JARVIS Implementation Roadmap

Tracks phase-by-phase status. See `ARCHITECTURE.md` for the full design.
Each phase ships as its own PR (or small series) and is not started until the
previous phase's modules have tests passing in CI.

| Phase | Scope | Status |
|---|---|---|
| 0 | Repo scaffolding, `core`, minimal `api` boot | ✅ Done |
| 1 | `security` spine, Postgres/Redis, `memory` (short-term + episodic + semantic) | ✅ Done |
| 2 | `brain` (LLM router, tool registry), `agents` (Coordinator, Planner, Reasoning), `/ws/chat` | ✅ Done |
| 3 | `system`, `web`, Research Agent, Coding Agent | ⬜ Not started |
| 4 | `automation`, `vision`, Automation Agent, Vision Agent | ⬜ Not started |
| 5 | `voice` (wake word, STT, TTS), `/ws/voice` | ⬜ Not started |
| 6 | `tasks` (queue/workers/scheduler), `plugins` | ⬜ Not started |
| 7 | `frontend` dashboard, `desktop` Electron shell | ⬜ Not started |
| 8 | Hardening: perf, e2e tests, CI/CD image publishing, deployment docs | ⬜ Not started |

## Phase 0 checklist

- [x] `ARCHITECTURE.md` — architecture & design decisions
- [x] `ROADMAP.md` — this file
- [x] Top-level repo scaffolding (`README.md`, `.gitignore`, `.env.example`,
      `docker-compose.yml`)
- [x] `backend/` Python package skeleton with all module directories stubbed
      (each with a `README.md` describing its future contents and build
      phase)
- [x] `core` module implemented: settings, logging, exceptions, DI container,
      event bus interface — with unit tests
- [x] `api` module: FastAPI app factory + `/health` endpoint — with tests
- [x] CI workflow: lint (ruff), type-check (mypy), test (pytest) on every PR

## Phase 1 checklist

- [x] `core` extended: Postgres/Redis/Chroma/LLM-provider settings,
      `core.db.Database` (async SQLAlchemy engine/session helper, portable
      between SQLite-in-tests and Postgres-in-production),
      `core.redis.create_redis_client`
- [x] `security` module implemented: `Role`/`RiskLevel` RBAC, `PermissionEngine`
      (allow / requires-confirmation / deny, with per-session "always allow"
      grants for dangerous tools), `AuditLog` (in-memory + SQL-backed,
      `redact()` helper), `SecretsVault` (Fernet encryption at rest) — with
      unit tests
- [x] `memory` module implemented: `ShortTermMemory` (Redis-backed
      conversation buffer), `EpisodicStore` (Postgres-backed durable memory:
      conversation/task/project/preference/summary), `SemanticMemory`
      (ChromaDB similarity search over caller-supplied embeddings) — with
      unit tests
- [x] Integration tests against real Postgres and Redis (skip locally when
      unreachable; CI runs them against real service containers)
- [x] CI extended with Postgres + Redis service containers

Deferred out of Phase 1 (tracked, not forgotten): Alembic migrations (no
schema has shipped to a real environment yet to migrate from), the
knowledge graph (needs an extraction step from `brain`/`agents` to populate
it — see `memory/README.md`), and the Sandbox Executor (nothing to sandbox
until `system` lands in Phase 3).

## Phase 2 checklist

- [x] `core` extended: `anthropic_model` setting (default `claude-opus-5`)
- [x] `brain` module implemented: `LLMProvider` protocol + `ClaudeProvider`
      adapter (non-streaming `anthropic.AsyncAnthropic`, tested with a fake
      client double — no real network calls), `LLMRouter` (named provider
      registry), `ToolRegistry` (wires tool calls through
      `security.PermissionEngine` + `AuditLog` — no domain tools registered
      yet, Phase 3+), `ConversationEngine` (assembles history from
      `ShortTermMemory`, calls the routed provider, persists both turns) —
      with unit tests
- [x] `agents` module implemented: `Agent` (system prompt + provider name
      over `ConversationEngine`), `create_coordinator` / `create_planner` /
      `create_reasoning_agent` factories — with unit tests
- [x] `api`: `WS /ws/chat` — one connection is one session; wired to the
      Coordinator with a DI seam (`create_app(coordinator=...)`) so tests
      never hit real Redis/Anthropic — with unit tests

Deferred out of Phase 2: OpenAI/Ollama provider adapters (Claude ships
first per ARCHITECTURE.md §4; same `LLMProvider` interface, add when
needed), streaming token-by-token replies over `/ws/chat` (current wire
format is whole-message request/reply — the simplest thing that proves the
stack end to end), and Research/Coding/Memory/Automation/Security/Vision
agents (each wraps a domain module — `web`/`system`/`automation`/`vision`
— that doesn't exist until Phases 3-4).

## Definition of done (every phase)

1. Code merged behind the module's public interface (`__init__.py` exports
   only what other modules should use).
2. Unit tests for business logic; integration tests for anything touching
   Postgres/Redis/Chroma/external APIs (run against containers in CI).
3. Module `README.md` describing responsibility, public interface, and
   configuration.
4. `ARCHITECTURE.md` updated if the phase changed a design decision.
5. CI green: lint, type-check, tests.
