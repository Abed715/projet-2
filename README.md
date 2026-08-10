# JARVIS

*Just A Rather Very Intelligent System* — a modular, production-oriented AI
assistant: conversation + long-term memory + voice + vision + computer
automation + multi-agent reasoning + a plugin system, built like a real
platform rather than a single chatbot script.

See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for the full design (module map,
data flow, security model, tech stack rationale) and
**[ROADMAP.md](./ROADMAP.md)** for what's built vs. planned.

> **Status: Phase 0 — foundation.** The repo scaffolding, the `core` module
> (settings/logging/DI/event bus), and a minimal `api` health-check service
> are implemented and tested. Everything else in `ARCHITECTURE.md` is
> designed but not yet built — see `ROADMAP.md` for build order.

## Repository layout

```
backend/    Python/FastAPI backend — one package per module (core, brain,
            memory, voice, vision, automation, web, system, plugins,
            security, api, agents, tasks)
frontend/   Next.js dashboard (not yet started — Phase 7)
desktop/    Electron shell (not yet started — Phase 7)
infra/      Dockerfiles, CI support files
docs/       API docs, architecture diagrams
```

## Quickstart (backend, current state)

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp ../.env.example ../.env   # fill in as needed

pytest                        # run the test suite
uvicorn jarvis.api.app:create_app --factory --reload
# -> GET http://localhost:8000/health
```

## Full stack (once later phases land)

```bash
cp .env.example .env
docker compose up --build
```

This brings up Postgres, Redis, ChromaDB, and the API. The frontend and
voice/vision services are added to the compose file as their phases ship
(see `ROADMAP.md`).

## Contributing / build philosophy

This project is built **one module at a time**: each module ships with unit
tests (and integration tests where it touches infra), a `README.md`
describing its responsibility and public interface, and green CI before the
next module starts. See `ARCHITECTURE.md §9` for the phase plan.
