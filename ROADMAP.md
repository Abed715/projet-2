# JARVIS Implementation Roadmap

Tracks phase-by-phase status. See `ARCHITECTURE.md` for the full design.
Each phase ships as its own PR (or small series) and is not started until the
previous phase's modules have tests passing in CI.

| Phase | Scope | Status |
|---|---|---|
| 0 | Repo scaffolding, `core`, minimal `api` boot | ✅ In progress (this PR) |
| 1 | `security` spine, Postgres/Redis, `memory` (short-term + episodic + semantic) | ⬜ Not started |
| 2 | `brain` (LLM router, tool registry), `agents` (Coordinator, Planner, Reasoning), `/ws/chat` | ⬜ Not started |
| 3 | `system`, `web`, Research Agent, Coding Agent | ⬜ Not started |
| 4 | `automation`, `vision`, Automation Agent, Vision Agent | ⬜ Not started |
| 5 | `voice` (wake word, STT, TTS), `/ws/voice` | ⬜ Not started |
| 6 | `tasks` (queue/workers/scheduler), `plugins` | ⬜ Not started |
| 7 | `frontend` dashboard, `desktop` Electron shell | ⬜ Not started |
| 8 | Hardening: perf, e2e tests, CI/CD image publishing, deployment docs | ⬜ Not started |

## Phase 0 checklist (this PR)

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

## Definition of done (every phase)

1. Code merged behind the module's public interface (`__init__.py` exports
   only what other modules should use).
2. Unit tests for business logic; integration tests for anything touching
   Postgres/Redis/Chroma/external APIs (run against containers in CI).
3. Module `README.md` describing responsibility, public interface, and
   configuration.
4. `ARCHITECTURE.md` updated if the phase changed a design decision.
5. CI green: lint, type-check, tests.
