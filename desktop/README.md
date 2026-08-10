# desktop (Electron shell)

**Status:** implemented (Phase 7). Wraps `frontend/`'s Next.js dashboard —
loads it by URL, same as any browser would, never by importing frontend or
backend code directly.

## What's here

```
desktop/
  src/main.ts             Main process: window, tray, global shortcut
  src/preload.ts           contextBridge — the only Node/Electron surface
                            exposed to the loaded page
  src/resolve-app-url.ts   Pure "which URL does the window load" logic
                            (unit tested; main.ts's app-lifecycle wiring
                            itself is verified manually/E2E, see below)
  assets/icon.png          App/tray icon
```

## Running it

```bash
cd frontend && npm run dev        # in one terminal — dashboard on :3000
cd desktop && npm start           # in another — builds + launches Electron
```

`npm start` runs `tsc` then `electron .`. In development, the main window
loads `http://localhost:3000` (the Next.js dev server) by default. To point
it at a different URL — a `next start` server, a deployed dashboard —
set `JARVIS_FRONTEND_URL`:

```bash
JARVIS_FRONTEND_URL=http://localhost:4000 npm start
```

`NODE_ENV=production` with no `JARVIS_FRONTEND_URL` set is a hard error
(see Design notes) rather than silently falling back to `localhost:3000`.

## Features

- **Window**: loads the dashboard by URL; `contextIsolation: true`,
  `nodeIntegration: false`, `sandbox: true` — the renderer gets no direct
  Node/Electron access beyond what `preload.ts` explicitly exposes via
  `contextBridge` (currently just `window.jarvis.platform`/`.versions`, a
  placeholder for whatever the dashboard needs from the shell later).
- **Tray icon**: shows/focuses the window, or quits, from a context menu.
- **Global shortcut**: `CommandOrControl+Shift+J` shows/hides the main
  window — a plain visibility toggle, **not** the voice wake word (see
  below).

## Design notes

- **Why the window loads a URL instead of bundling a static export:**
  `frontend/` isn't configured for `next export`, and even if it were,
  Phase 7's dashboard is deliberately non-static in spirit (it's designed
  to talk to a live backend over WS `/ws/chat`). Packaging a specific
  frontend build *into* the Electron app (static export, or an embedded
  `next start` server spawned as a child process) is real, undecided
  packaging work — this phase ships a working shell against a
  separately-run frontend, matching how every other "not yet decided"
  deployment question in this repo has been left explicit rather than
  guessed at. `resolveAppUrl`'s hard error in production (no silent
  `localhost` fallback) is there so this gap fails loudly instead of
  quietly shipping a broken production build.
- **Why the global shortcut isn't wired to the voice wake word:**
  ARCHITECTURE.md's Phase 7 scope describes "global hotkey for the voice
  wake word." `voice.OpenWakeWordDetector` (Phase 5) is a complete, tested
  component, but nothing continuously feeds it microphone audio — that
  needs a persistent capture loop, which belongs on a client (this one),
  not the backend's request/reply `/ws/voice` endpoint. Building that loop
  is a real feature, not a rename of the existing hotkey; until it exists,
  the hotkey does the one honest thing available to it: toggle window
  visibility, a normal and useful Electron tray-app pattern on its own.
- **Why `resolveAppUrl` is a separate, pure function:** `main.ts` itself
  (window/tray/shortcut lifecycle) is Electron-API-shaped code that's
  expensive to unit test meaningfully without mocking most of Electron;
  pulling the one piece of actual decision logic ("which URL do we load,
  and when should that be a hard error") out into a pure function keeps
  it unit-tested without pretending to unit-test Electron's own APIs.

## Known limitations / deferred

- No packaged/installable build (`electron-builder`/`electron-forge`) —
  `npm start` runs from source. Packaging is meaningful work of its own
  (per-platform code signing, auto-update, installer UX) with no concrete
  target platform decided yet.
- No native notifications wiring yet — Electron's `Notification` API is
  straightforward to add once there's a concrete event to notify about
  (e.g. a `/ws/chat` disconnect, or a completed background task once
  `jarvis.api` exposes `tasks` — see `backend/src/jarvis/tasks/README.md`).
- No auto-updater.
- Global-shortcut-to-wake-word wiring (see Design notes above).
- Verified manually in this repo's dev sandbox: `tsc` build succeeds, the
  packaged `electron .` process starts and stays running against a live
  `next dev` server with no errors (headless via `Xvfb`, since this
  sandbox has no display). Full interactive verification (actually
  clicking the tray icon, pressing the hotkey) needs a real display and
  hasn't been done here — normal for a headless CI-style environment, but
  worth doing once before relying on this for real use.
