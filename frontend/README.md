# frontend (Next.js dashboard)

**Status:** not yet started — planned for **Phase 7** of the roadmap.

Will host the JARVIS dashboard: conversation timeline, memory viewer, running
tasks, system status (CPU/GPU/RAM/temperature/internet), plugin manager,
voice animation, dark mode. Talks to the backend only through its public
REST/WebSocket API (`backend/src/jarvis/api`) — never by importing backend
code.

See [`ARCHITECTURE.md`](../ARCHITECTURE.md) and [`ROADMAP.md`](../ROADMAP.md).
