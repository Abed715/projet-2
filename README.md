# JARVIS

*Just A Rather Very Intelligent System* — a modular, production-oriented AI
assistant: conversation + long-term memory + voice + vision + computer
automation + multi-agent reasoning + a plugin system, built like a real
platform rather than a single chatbot script.

See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for the full design (module map,
data flow, security model, tech stack rationale) and
**[ROADMAP.md](./ROADMAP.md)** for what's built vs. planned.

> **Status: Phase 7 done — Jarvis can research, code, control the
> computer, see the screen, talk, run background jobs, load plugins, and
> now has a dashboard and a desktop shell to talk to it through.**
> `core`, `security` (incl. a sandboxed subprocess executor), `memory`,
> `brain` (Claude-backed LLM router, tool registry, and a real agentic
> tool-use loop), `agents` (Coordinator/Planner/Reasoning for chat, plus
> Research/Coding/Automation/Vision agents that actually call tools),
> `system` (sandboxed shell + workspace-confined file ops), `web` (fetch +
> search, no API key required), `automation` (process management,
> clipboard, notifications, keyboard/mouse control), `vision` (OCR, image
> analysis, screen capture, window detection), `voice` (Whisper STT,
> Piper TTS, wake-word detection), `tasks` (Redis Streams job queue,
> workers, interval scheduler, retry/pause/resume/cancel), and `plugins`
> (manifest + loader + a working GitHub reference plugin) are implemented
> and tested (274 backend tests, `ruff`/`mypy --strict` clean). `frontend`
> (Next.js dashboard: live Chat page over `WS /ws/chat`, dark mode,
> honest "coming soon" pages for the modules with no REST surface yet) and
> `desktop` (Electron shell: tray icon, global shortcut, sandboxed
> renderer) are implemented and tested too (18 frontend + 4 desktop
> tests). `WS /ws/chat` works end to end with `ANTHROPIC_API_KEY` set;
> `WS /ws/voice` works once `JARVIS_PIPER_VOICE_MODEL_PATH` is set.
> Everything else in `ARCHITECTURE.md` is designed but not yet built —
> see `ROADMAP.md` for build order and what's next (Phase 8: hardening).

## Repository layout

```
backend/    Python/FastAPI backend — one package per module (core, brain,
            memory, voice, vision, automation, web, system, plugins,
            security, api, agents, tasks)
frontend/   Next.js dashboard (Phase 7) — talks to the backend only via
            its public REST/WebSocket API
desktop/    Electron shell (Phase 7) — wraps the frontend build
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
# -> WS  ws://localhost:8000/ws/chat   (needs ANTHROPIC_API_KEY in .env to get real replies)
# -> WS  ws://localhost:8000/ws/voice  (needs JARVIS_PIPER_VOICE_MODEL_PATH in .env, plus
#                                        ANTHROPIC_API_KEY for the reply — otherwise closes
#                                        with code 1011 "voice not configured")
```

## Quickstart (frontend + desktop)

Requires Node.js 22+. Run alongside the backend above.

```bash
cd frontend
npm install
cp ../.env.example .env.local   # sets NEXT_PUBLIC_API_BASE_URL
npm run dev                      # -> http://localhost:3000
```

```bash
cd desktop
npm install
npm start   # builds + launches an Electron window loading the dashboard
```

See `frontend/README.md` and `desktop/README.md` for what's live vs.
"coming soon" and why.

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
