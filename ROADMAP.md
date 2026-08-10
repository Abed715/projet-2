# JARVIS Implementation Roadmap

Tracks phase-by-phase status. See `ARCHITECTURE.md` for the full design.
Each phase ships as its own PR (or small series) and is not started until the
previous phase's modules have tests passing in CI.

| Phase | Scope | Status |
|---|---|---|
| 0 | Repo scaffolding, `core`, minimal `api` boot | ✅ Done |
| 1 | `security` spine, Postgres/Redis, `memory` (short-term + episodic + semantic) | ✅ Done |
| 2 | `brain` (LLM router, tool registry), `agents` (Coordinator, Planner, Reasoning), `/ws/chat` | ✅ Done |
| 3 | `system`, `web`, Research Agent, Coding Agent | ✅ Done |
| 4 | `automation`, `vision`, Automation Agent, Vision Agent | ✅ Done |
| 5 | `voice` (wake word, STT, TTS), `/ws/voice` | ✅ Done |
| 6 | `tasks` (queue/workers/scheduler), `plugins` | ✅ Done |
| 7 | `frontend` dashboard, `desktop` Electron shell | ✅ Done |
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

## Phase 3 checklist

- [x] `security` extended: `SandboxExecutor` (argv-only subprocess
      execution confined to a workspace directory, minimal explicit env,
      timeout — process-level isolation, not OS-level sandboxing; see
      `security/README.md`) — with unit tests
- [x] `brain` extended: `ToolSpec.input_schema` (JSON schema per tool, for
      Claude's `tools` parameter), `ToolRunner` (hand-written agentic
      tool-use loop — not the SDK's beta tool runner, since JARVIS's
      confirmation semantics aren't something a generic runner knows
      about; every tool call still goes through `ToolRegistry` for
      permission + audit; `DANGEROUS` tools pending confirmation stop the
      loop cleanly rather than guessing; `allowed_tools` scopes which
      tools an agent can see and enforces it defense-in-depth) — with unit
      tests against a fake Anthropic client (no real network calls)
- [x] `system` module implemented: `FilesystemService` (path-traversal-safe,
      workspace-confined read/write/list/move/delete), `ShellService`
      (over `SandboxExecutor`), `register_system_tools` (`read_file`/
      `list_dir` SAFE, `write_file`/`move_file` SENSITIVE, `delete_file`/
      `run_shell_command` DANGEROUS) — with unit tests
- [x] `web` module implemented: `parse_html` (dependency-free HTML → text/
      table extraction via stdlib `html.parser`), `WebAgent` (`fetch` with
      a best-effort SSRF guard, `search` delegating to a `SearchProvider`),
      `DuckDuckGoSearchProvider` (no API key required), `register_web_tools`
      (`web_search`/`web_fetch`, both SENSITIVE) — with unit tests against
      `httpx.MockTransport` (no real network calls)
- [x] `agents` extended: `ToolAgent` (system prompt + role + `ToolRunner`,
      the tool-using counterpart to Phase 2's plain-chat `Agent`),
      `create_research_agent` (scoped to `web_search`/`web_fetch`),
      `create_coding_agent` (scoped to `system`'s file/shell tools) — with
      unit tests

Deferred out of Phase 3: wiring Research/Coding agents into `jarvis.api`
(no REST/WS surface change was committed for this phase; they're usable
directly and will get an API surface once Coordinator gains delegation),
resuming a `ToolRunner` loop after a pending confirmation is granted (needs
the task engine's pause/resume, Phase 6), and process management
(open/close applications — waits on `automation`'s OS-level primitives,
Phase 4).

## Phase 4 checklist

- [x] `automation` module implemented: `ProcessService` (open/close/list
      processes via `psutil`/`subprocess`, headless-safe — no backend
      Protocol needed), `ClipboardService`/`NotificationService`/
      `InputService` each over a swappable backend Protocol (real backend —
      `pyperclip`/`notify-send`/`pyautogui` — lazily constructed or called,
      translating headless failures into `ConfigurationError`),
      `register_automation_tools` (`list_processes`/`send_notification`
      `SAFE`, `clipboard_read`/`clipboard_write`/`mouse_move` `SENSITIVE`,
      `open_application`/`close_application`/`mouse_click`/`type_text`/
      `press_key` `DANGEROUS`) — with unit tests
- [x] `vision` module implemented: `OcrService` (`pytesseract` + Pillow,
      real headless OCR, verified against the `tesseract-ocr` system
      package), `ImageAnalysisService` (Pillow: dimensions, format, average
      color), `ScreenCaptureService`/`WindowDetectionService` each over a
      swappable backend Protocol (real backend — `mss`/`wmctrl` — lazily
      constructed, translating headless/missing-binary failures into
      `ConfigurationError`), `register_vision_tools` (`extract_text`/
      `analyze_image` `SAFE`, `capture_screen`/`list_windows` `SENSITIVE`)
      — with unit tests, including real OCR/image-analysis round-trips
      against synthetically generated images (no fakes needed there — both
      are headless-safe)
- [x] `agents` extended: `create_automation_agent` (scoped to
      `automation`'s tools), `create_vision_agent` (scoped to `vision`'s
      tools, read-only by design) — with unit tests
- [x] CI extended: installs the `tesseract-ocr` system package before
      running tests

Deferred out of Phase 4: object detection and webcam/live camera input
(no CV model or capture-device dependency has been added yet — see
`vision/README.md`), macOS/Windows backends for clipboard/input/
notifications/window-detection beyond what `pyperclip`/`pyautogui` already
handle cross-platform (Linux/X11 is the only target verified so far — see
`automation/README.md` and `vision/README.md`), and reaping child processes
spawned by `open_application` (no task-engine process tracking yet, Phase
6).

## Phase 5 checklist

- [x] `core` extended: `whisper_model_size` (default `"small"`) and
      `piper_voice_model_path` (default unset) settings
- [x] `voice` module implemented: `STTProvider`/`TTSProvider` protocols
      (mirrors `brain.providers.base.LLMProvider`'s provider-abstraction
      pattern), `FasterWhisperSTTProvider`/`PiperTTSProvider` (real
      adapters over `faster_whisper`/`piper`, constructed from an
      already-loaded model — never loaded by the provider itself, so unit
      tests never download real model weights), `WakeWordDetector`
      protocol + `OpenWakeWordDetector` (same already-loaded-model
      pattern, over `openwakeword`), `VoicePipeline` (non-streaming
      transcribe → `ConversationalAgent.respond` → synthesize turn,
      analogous to how `/ws/chat` composes `ConversationEngine`) — with
      unit tests against fake model/coordinator doubles
- [x] `api` extended: `WS /ws/voice` (binary audio in, binary audio out,
      one connection is one session — same model as `/ws/chat`), lazily
      builds the real `VoicePipeline` on first connection instead of at
      `create_app()` time (loading real STT/TTS models is a genuine
      network/CPU-heavy operation, unlike the coordinator's lazy client
      handles), closes cleanly with code `1011` /
      `"voice not configured"` when `JARVIS_PIPER_VOICE_MODEL_PATH` isn't
      set — with unit tests against a fake `VoicePipeline`

Deferred out of Phase 5: streaming partial transcripts, voice activity
detection (VAD) for automatic end-of-utterance, barge-in/interrupt
(stopping TTS playback when the user starts talking again), emotion
tagging, and wiring `OpenWakeWordDetector` into `/ws/voice` or any
always-listening loop (continuous wake-word listening needs a persistent
audio-frame stream and activation state machine that belongs in a client —
the Electron shell, Phase 7 — not the request/reply backend endpoint; see
`voice/README.md`). Also deferred: an ElevenLabs `TTSProvider` adapter
(optional cloud alternative to Piper per ARCHITECTURE.md §4, add when
higher voice quality is actually needed).

## Phase 6 checklist

- [x] `tasks` module implemented: `Task`/`TaskStatus` model, `TaskStore`
      (Postgres/SQLite via `core.db.Database`, mirrors
      `memory.episodic.EpisodicStore`), `TaskQueue` (Redis Streams
      consumer groups over a narrow `StreamLike` protocol, mirrors
      `memory.short_term.RedisLike` — tested against `fakeredis`, which
      fully supports Streams/consumer groups, no real Redis server),
      `TaskEngine` (submit/run_once/pause/resume/cancel + a per-task-name
      handler registry, with retry-until-`max_attempts` on handler
      failure), `TaskWorker` (poll loop over `run_once`), `Scheduler`
      (interval-based recurring submission — simplified "cron-like" per
      ARCHITECTURE.md, no cron-expression parser added) — with unit tests
- [x] `plugins` module implemented: `PluginManifest` (declarative
      metadata only — not a trust boundary), `Plugin` protocol
      (`manifest` + `register_tools(registry)`), `PluginLoader`
      (register/load_all/list_plugins), `GitHubPlugin` (the one reference
      plugin: public repo lookups via an injected `httpx.AsyncClient`,
      tested against `httpx.MockTransport`) — with unit tests proving a
      plugin's tool goes through the exact same `ToolRegistry`/
      `PermissionEngine`/`AuditLog` path as any built-in module's tools,
      with no plugin-specific security plumbing added

Deferred out of Phase 6: exponential backoff on task retry, dead-letter
handling beyond `FAILED` status, full cron expression syntax for
`Scheduler`, a `jarvis.api` surface for submitting/inspecting tasks or
managing plugins externally, Planner-to-Task-Engine delegation (this
phase ships the engine, not its first caller — see `tasks/README.md`),
and plugin discovery/hot-loading from disk (plugins are registered as
already-instantiated objects; a manifest-file scanner/installer is a
Phase 7 frontend-plugin-manager concern, see `plugins/README.md`).

## Phase 7 checklist

- [x] `frontend` implemented: Next.js 16 (App Router) + TypeScript +
      TailwindCSS v4 dashboard. Sidebar nav (Overview/Chat/Memory/Tasks/
      Plugins/System), dark mode (custom `ThemeProvider` + pre-hydration
      `ThemeScript`, no `next-themes` dependency needed for ~60 lines of
      logic), `useChatSocket` (WebSocket hook wired to the real `WS
      /ws/chat` endpoint — connection status, message history, send) —
      the one live dashboard feature this phase ships, since it's the one
      backend surface that actually exists to connect to. Memory/Tasks/
      Plugins/System are honest "coming soon" pages, not fake data —
      `jarvis.api` has no REST surface for those modules yet (see Phase 6
      deferrals above). Unit tested (Vitest + React Testing Library, fake
      `WebSocket` double — no real network calls), verified end-to-end in
      a real browser against a live backend (`ruff`-equivalent: ESLint;
      `mypy --strict`-equivalent: `tsc --noEmit`, both clean)
- [x] `desktop` implemented: Electron shell loading the dashboard by URL
      (`JARVIS_FRONTEND_URL`, defaults to `http://localhost:3000` in dev;
      hard error in production with nothing configured, rather than a
      silent wrong-URL fallback), `contextIsolation`/sandboxed renderer
      with a minimal `preload.ts` bridge, tray icon (show/quit), global
      shortcut (window show/hide toggle — explicitly not the voice wake
      word, see `desktop/README.md`). `resolveAppUrl`'s decision logic
      unit tested; full app lifecycle verified by an actual headless
      launch (`Xvfb`) staying up against a live `next dev` server with no
      errors
- [x] CI: `frontend-ci.yml` (lint, type-check, test, build) and
      `desktop-ci.yml` (type-check, test, build) added, mirroring
      `backend-ci.yml`'s structure

Deferred out of Phase 7: REST endpoints in `jarvis.api` for memory/tasks/
plugins/system (blocks the corresponding dashboard panels — frontend work
is done, backend surface isn't there yet), voice UI (mic capture/playback
wired to `/ws/voice`), streaming token-by-token chat replies (inherited
from `/ws/chat`'s own Phase 2 scope), packaged/installable Electron builds
(`electron-builder`/`electron-forge`, code signing, auto-update — no
target platform decided), global-shortcut-to-wake-word wiring (needs a
continuous microphone-capture loop that doesn't exist on any client yet),
and native desktop notifications (straightforward to add once there's a
concrete event to notify about).

## Definition of done (every phase)

1. Code merged behind the module's public interface (`__init__.py` exports
   only what other modules should use).
2. Unit tests for business logic; integration tests for anything touching
   Postgres/Redis/Chroma/external APIs (run against containers in CI).
3. Module `README.md` describing responsibility, public interface, and
   configuration.
4. `ARCHITECTURE.md` updated if the phase changed a design decision.
5. CI green: lint, type-check, tests.
