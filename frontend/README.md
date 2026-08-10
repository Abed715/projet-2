# frontend (JARVIS dashboard)

**Status:** implemented (Phase 7): Next.js 16 (App Router) + TypeScript +
TailwindCSS v4. Talks to the backend only through its public REST/WebSocket
API (`backend/src/jarvis/api`) — never by importing backend code.

## Running it

```bash
npm install
cp ../.env.example .env.local   # sets NEXT_PUBLIC_API_BASE_URL
npm run dev                      # http://localhost:3000
```

Requires the backend running (`cd backend && uvicorn jarvis.api.app:create_app
--factory`) for the Chat page to actually connect — see the top-level
`README.md`'s quickstart.

Other scripts: `npm run build` (production build), `npm run lint` (ESLint),
`npm test` (Vitest + React Testing Library, single run), `npm run
test:watch` (watch mode).

## What's here

```
src/
  app/                  Routes (App Router): / (overview), /chat (live),
                         /memory, /tasks, /plugins, /system (all "coming
                         soon" placeholders — see Design notes)
  components/
    chat/                ChatMessage, ChatTimeline, ChatInput,
                          ConnectionStatusBadge
    layout/               Sidebar (nav), ComingSoon (placeholder page body)
    theme/                ThemeProvider/useTheme, ThemeToggle, ThemeScript
                          (pre-hydration dark-mode class, avoids a flash
                          of the wrong theme)
  hooks/
    use-chat-socket.ts    WebSocket connection to /ws/chat: connection
                          status, message history, sendMessage
  lib/
    config.ts             getApiBaseUrl/getWsUrl — the one place the
                          backend's base URL is read from
                          NEXT_PUBLIC_API_BASE_URL
```

## Public interface (what talks to the backend)

- **`useChatSocket({ path = "/ws/chat", createSocket? })`** — opens a
  WebSocket to the backend, exposes `{ status, messages, sendMessage }`.
  `createSocket` is a dependency-injection seam (defaults to a real
  browser `WebSocket` wrapped in the hook's own `SocketLike` shape) so
  tests drive the hook with a fake socket — no real network connection in
  the test suite, same "no real I/O in tests" rule the backend follows.
- **`getApiBaseUrl()` / `getWsUrl(path)`** (`lib/config.ts`) — read
  `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`) and derive
  the matching `ws(s)://` URL for a given backend route.

## Design notes

- **Why only `/chat` is live and `/memory`, `/tasks`, `/plugins`,
  `/system` are "coming soon" pages instead of connected panels:** each of
  those backend modules (`memory`, `tasks`, `plugins`) is fully
  implemented and tested (Phases 1, 6), but `jarvis.api` has no REST
  surface exposing them yet — Phase 6's own ROADMAP entry explicitly
  deferred that REST surface as separate work from the Task Engine/plugin
  loader themselves. Building dashboard panels against endpoints that
  don't exist would mean either fabricating fake data or leaving dead UI
  — neither is honest. `/system` has the same gap: `automation.
  ProcessService` can list OS processes, but there's no CPU/RAM/GPU
  metrics endpoint. `/chat` is the one dashboard feature with a real,
  working backend endpoint (`WS /ws/chat`, Phase 2), so it's the one
  real, working feature this phase ships.
- **Why dark mode uses a custom `ThemeProvider` instead of `next-themes`:**
  the whole toggle is ~60 lines (read `localStorage`/`prefers-color-scheme`,
  toggle a `.dark` class, persist the choice) and Tailwind v4's
  `@custom-variant dark (&:where(.dark, .dark *))` does the rest — a
  dependency wasn't needed for something this small. `ThemeScript` (an
  inline `<script>` in `<head>`, not part of the React tree) sets the
  class *before* hydration so a dark-system-preference user doesn't see a
  flash of the light theme.
- **Why `useChatSocket` wraps the real `WebSocket` instead of using it
  directly:** `SocketLike` is a narrow interface (`send`/`close`/four
  `on*` callbacks) that a real browser `WebSocket` doesn't structurally
  satisfy as-is (its native `on*` properties carry a `this: WebSocket` DOM
  event signature) — `createBrowserSocket` adapts it via
  `addEventListener` once, in one place, so the hook's own logic never
  touches the DOM `WebSocket` type directly and stays trivially testable
  with a fake `SocketLike`.

## Known limitations / deferred

- Memory/Tasks/Plugins/System panels (see Design notes) — blocked on
  `jarvis.api` REST endpoints that don't exist yet, not on frontend work.
- No streaming token-by-token chat replies — `/ws/chat` itself is
  whole-message request/reply (Phase 2's deliberate scope), so the
  frontend can't display partial replies even if it wanted to.
- No voice UI (`/ws/voice` mic capture + playback) — the backend endpoint
  exists (Phase 5), but capturing/playing audio from the browser and
  wiring it to a binary WebSocket is a real feature this phase didn't
  build; `/chat`'s text-only round trip was the one proven end-to-end.
- No auth/session persistence across page reloads — every page load opens
  a fresh `/ws/chat` connection (a fresh session server-side too, per
  `api/README.md`).
