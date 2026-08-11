# Deployment

Three things can be deployed independently: the **backend** (FastAPI +
Postgres + Redis + ChromaDB), the **frontend** (Next.js dashboard), and the
**desktop** shell (Electron, wraps the frontend). All three are covered
below for Linux, Windows, and macOS.

## The short version

```bash
git clone <this repo>
cd projet-2
cp .env.example .env   # fill in ANTHROPIC_API_KEY at minimum
docker compose up --build
# -> http://localhost:8000/health  (backend)
# -> http://localhost:3000         (dashboard)
```

This works identically on Linux, macOS, and Windows (via Docker Desktop) —
see [Docker Compose (all platforms)](#docker-compose-all-platforms) below
for what each service is and how to configure it.

## What's verified vs. not

Everything in this document is either directly executed and observed in
this repo's own development/CI environment, or explicitly marked as not
yet verified. In particular:

- `backend/pyproject.toml`'s dependency install, the full `pytest` suite
  (unit + integration + e2e, 279 tests), and the real out-of-process
  `uvicorn` subprocess used by `tests/e2e` are all genuinely exercised —
  see `backend/tests/e2e/README.md`.
- `infra/docker/backend.Dockerfile` and `infra/docker/frontend.Dockerfile`
  were written and carefully reviewed, and the exact runtime artifact each
  one packages was independently verified where possible without a
  container build (the backend's `pip install --prefix=/install .`
  pattern mirrors the project's own proven local install; the frontend's
  `.next/standalone/server.js` was run directly with `node` and served
  every route correctly). Actually running `docker build` against these
  files was not possible in this project's development sandbox — its
  network egress policy blocks Docker Hub's CDN
  (`production.cloudfront.docker.com`), so base images (`python:3.11-slim`,
  `node:22-slim`) couldn't be pulled there. This is a constraint of that
  one environment, not of the Dockerfiles or of GitHub Actions (where
  `publish-images.yml` runs these same builds for real, with normal
  registry access). **If you're deploying from a fresh clone, your first
  `docker compose up --build` is the first real end-to-end build+run of
  these images — watch its output.**
- Windows- and macOS-native (non-Docker) instructions below follow the
  same commands documented by Docker/Node/Python's own official docs for
  those platforms; they haven't been run on real Windows/macOS machines
  from this repo.

## Docker Compose (all platforms)

Requires [Docker](https://docs.docker.com/get-docker/) (Docker Desktop on
Windows/macOS, Docker Engine on Linux) with Compose v2.

```bash
cp .env.example .env   # fill in ANTHROPIC_API_KEY, JARVIS_SECRET_KEY, etc.
docker compose up --build
```

Brings up `postgres`, `redis`, `chroma`, `api` (backend, built from
`infra/docker/backend.Dockerfile`), and `frontend` (built from
`infra/docker/frontend.Dockerfile`). Ports published to the host:

| Service | Port | Notes |
|---|---|---|
| `api` | 8000 | `GET /health`, `WS /ws/chat`, `WS /ws/voice` |
| `frontend` | 3000 | The dashboard |
| `postgres` | 5432 | |
| `redis` | 6379 | |
| `chroma` | 8001 | |

**`NEXT_PUBLIC_API_BASE_URL` is baked into the frontend image at build
time, not read at container runtime** (standard Next.js behavior — see
`infra/docker/frontend.Dockerfile`'s top comment). The compose file passes
it as a `build.args` value, defaulting to `http://localhost:8000` — correct
when your browser and the `api` container's published port are both on
`localhost`. Deploying frontend and backend to different hosts means
setting `NEXT_PUBLIC_API_BASE_URL` in `.env` to wherever your **browser**
can reach the backend (not the `api` service's internal Docker network
name — the browser can't resolve that) *before* running `docker compose
build`.

Stop everything: `docker compose down`. Add `-v` to also drop the
Postgres/Redis/Chroma volumes.

## Using published images instead of building locally

`.github/workflows/publish-images.yml` builds and pushes
`ghcr.io/<owner>/<repo>/backend` and `ghcr.io/<owner>/<repo>/frontend` on
every push to `main` (tagged `latest` and the commit SHA) and on version
tags (`v*`). Once a repo has run that workflow at least once:

```bash
docker pull ghcr.io/<owner>/<repo>/backend:latest
docker pull ghcr.io/<owner>/<repo>/frontend:latest
```

The published `frontend` image was built with
`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` unless the repo sets a
`NEXT_PUBLIC_API_BASE_URL` Actions variable — see `publish-images.yml`'s
comment on that build arg. If your deployment needs a different value,
build your own image from `infra/docker/frontend.Dockerfile` with the
right `--build-arg` rather than using the published one.

## Linux (native, no Docker)

```bash
# Postgres + Redis, via your distro's package manager, e.g. on Debian/Ubuntu:
sudo apt-get install postgresql redis-server tesseract-ocr
sudo systemctl enable --now postgresql redis-server

cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
cp ../.env.example ../.env   # fill in; POSTGRES_HOST/REDIS_HOST default to localhost
uvicorn jarvis.api.app:create_app --factory --host 0.0.0.0 --port 8000
```

For a persistent service, run that last command under a `systemd` unit
(`ExecStart=/path/to/.venv/bin/uvicorn ...`, `Restart=on-failure`) rather
than a foreground terminal — `infra/docker/backend.Dockerfile`'s `CMD` is
the canonical invocation to mirror.

`jarvis.automation`/`jarvis.vision`'s optional OS-level backends
(`notify-send`, `wmctrl`, clipboard/input control) are Linux/X11-targeted
already — see `automation/README.md` and `vision/README.md` for exactly
what's supported and what raises `ConfigurationError` instead. Frontend:
same `npm run build && npm start` as any Next.js app, or serve
`infra/docker/frontend.Dockerfile`'s image behind nginx/Caddy.

## Windows

**Recommended: Docker Desktop with the WSL2 backend.** Install [Docker
Desktop](https://docs.docker.com/desktop/setup/install/windows-install/),
enable WSL2 integration, then follow [Docker Compose (all
platforms)](#docker-compose-all-platforms) above from a WSL2 terminal (or
PowerShell — Docker Desktop exposes the same `docker`/`docker compose`
CLI either way).

**Native (no Docker), if you need it:** Python 3.11+ and Node.js 22+ both
install and run on Windows directly, and the backend has no Linux-only
*dependency* — but `jarvis.automation`'s real backends
(`PyAutoGuiInputBackend`, `DesktopNotificationBackend`) and
`jarvis.vision`'s (`MssScreenCaptureBackend`, `WmctrlWindowDetectionBackend`)
were only verified against Linux/X11 (see the "Known limitations" section
of each module's README) — `pyautogui`/`mss` themselves are
cross-platform and should work on Windows as-is, but `notify-send` and
`wmctrl` are Linux-only and will raise `ConfigurationError` there; a
Windows-native notification/window-listing backend is real work this
project hasn't done yet. Postgres and Redis both ship native Windows
builds if you'd rather not use Docker for just those two.

**Desktop shell:** `cd desktop && npm install && npm start` runs from
source on Windows the same as anywhere else Electron runs. There's no
packaged Windows installer (`.exe`/MSIX) yet — see
`desktop/README.md`'s "Known limitations."

## macOS

**Recommended: Docker Desktop.** Install [Docker
Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), then
follow [Docker Compose (all platforms)](#docker-compose-all-platforms).

**Native (no Docker), if you need it:**

```bash
brew install postgresql@16 redis tesseract
brew services start postgresql@16
brew services start redis

cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
cp ../.env.example ../.env
uvicorn jarvis.api.app:create_app --factory --host 0.0.0.0 --port 8000
```

Same automation/vision platform caveat as Windows: `pyautogui`/`mss` are
cross-platform, but `automation.DesktopNotificationBackend`
(`notify-send`) and `vision.WmctrlWindowDetectionBackend` (`wmctrl`) are
Linux-only today. macOS equivalents (`osascript`/`terminal-notifier` for
notifications, `NSWorkspace`/Quartz APIs for window listing) are real
features this project hasn't built — see each module's README.

**Desktop shell:** `cd desktop && npm install && npm start`. No packaged
`.dmg`/`.app` yet (same gap as Windows — `desktop/README.md`).

## Load/perf checking a deployment

`backend/scripts/perf_smoke.py` is a standalone script (not part of the
test suite — see its module docstring for why) that load-tests an
already-running backend:

```bash
python backend/scripts/perf_smoke.py --base-url http://localhost:8000
```

Point it at a deployment (Docker Compose, a native install, a staging
environment) after a change you suspect affects the hot path, to catch
gross regressions before/after comparison. It is not a calibrated
benchmark and CI does not gate on its output.
