# jarvis.tasks

**Status:** implemented (Phase 6). Depends on `jarvis.core` only (`Database`
for durable metadata, the exception hierarchy). Nothing above `core`
imports into this module — it's a generic execution substrate, not tied to
any domain module's tools.

## Public interface

```python
from jarvis.tasks import (
    Task, TaskStatus,
    TaskStore,
    StreamLike, TaskQueue,
    TaskEngine, TaskHandler,
    TaskWorker,
    Scheduler,
)
```

- **`Task`** / **`TaskStatus`** — the data model. `TaskStatus`:
  `PENDING → RUNNING → COMPLETED | FAILED`, plus `PAUSED` (only reachable
  from `PENDING`) and `CANCELLED` (only reachable from `PENDING`/`PAUSED`).
- **`TaskStore(database)`** — durable task metadata (status, attempt count,
  result/error), Postgres in production / SQLite in tests via
  `core.db.Database` — same pattern as `memory.episodic.EpisodicStore`.
- **`StreamLike`** — the narrow `Protocol` subset of `redis.asyncio.Redis`'s
  Streams API (`xadd`/`xgroup_create`/`xreadgroup`/`xack`) this module
  needs, same pattern as `memory.short_term.RedisLike`. **`TaskQueue`**
  wraps it: a Redis Streams consumer group gives at-least-once delivery —
  a dequeued-but-unacked message is redelivered on worker crash/restart,
  not silently dropped.
- **`TaskEngine(*, store, queue)`** — the coordinator. `register_handler(name,
  handler)` maps a task name to an async `payload -> result` function.
  `submit(name, payload, *, max_attempts=3)` persists a `PENDING` task and
  enqueues it. `run_once(consumer_name)` dequeues and processes exactly one
  task — retrying on handler exceptions up to `max_attempts` before marking
  `FAILED` — and is what both `TaskWorker`'s loop and tests call.
  `pause`/`resume`/`cancel` operate on stored status; see the limitation
  below.
- **`TaskWorker(engine, *, consumer_name, poll_interval_seconds=1.0)`** —
  `run(stop_event: asyncio.Event)` polls `run_once` until told to stop,
  sleeping only when the queue was empty so a backlog drains back-to-back.
- **`Scheduler(engine)`** — `register(name, payload, *, interval_seconds,
  start_immediately=True)` then `tick(now=...)` submits every entry whose
  interval has elapsed and reschedules it. No internal timer — call `tick`
  periodically (e.g. from the same loop that runs a `TaskWorker`).

## Design notes

- **Why a `Protocol` for Streams instead of importing `redis.asyncio.Redis`
  directly:** identical reasoning to `RedisLike` in `memory.short_term` —
  it lets tests inject `fakeredis.aioredis.FakeRedis`, which fully supports
  Streams and consumer groups, so the whole module is tested with zero
  real Redis server (verified directly: `xadd`/`xreadgroup`/`xack`/
  `xgroup_create`, including the `BUSYGROUP` re-creation path, all behave
  identically against `fakeredis`).
- **Why task metadata lives in `TaskStore` (Postgres/SQLite) instead of in
  the stream itself:** Streams are a delivery mechanism, not a queryable
  system of record — `list_by_status`, retry counts, and results need a
  real table. This mirrors why `memory` splits `ShortTermMemory` (Redis,
  ephemeral) from `EpisodicStore` (Postgres, durable) rather than making
  one module do both jobs.
- **Retry semantics:** a failing handler's task goes back to `PENDING` and
  is re-enqueued immediately (no backoff/delay) until `attempt >=
  max_attempts`, then `FAILED`. Exponential backoff is a real feature this
  simple version doesn't have yet — every current use case tolerates
  immediate retry; add delay scheduling if a handler that needs it shows
  up.
- **`cancel()` only accepts `PENDING`/`PAUSED` tasks, not `RUNNING`:** a
  running task's handler has no cooperative cancellation hook — there's
  nothing to interrupt it mid-flight, and flipping its stored status while
  `run_once` is still awaiting the handler would just get overwritten by
  `run_once`'s own final status update once the handler returns. Same
  category of limitation as `security.SandboxExecutor`'s "process-level
  isolation, not true interruption" — documented rather than faked.
- **Scheduler is interval-based, not full cron syntax:** ARCHITECTURE.md
  calls it "cron-like"; this ships fixed-interval recurring tasks (no new
  cron-parsing dependency) because every concrete use case so far is "run
  X every N minutes/hours." A real cron expression parser is a drop-in
  upgrade to `Scheduler.register`'s signature if/when a use case actually
  needs day-of-week/month scheduling.

## Known limitations / deferred

- No exponential backoff on retry (see above).
- No dead-letter handling beyond `FAILED` status — a permanently-failed
  task just sits there for a caller to notice via `list_by_status`, there's
  no separate dead-letter stream.
- Full cron expression syntax (see Scheduler note above).
- No REST/WS surface in `jarvis.api` yet for submitting/inspecting tasks
  externally — `TaskEngine` is usable directly by other backend code (the
  Planner delegating multi-step work, per ARCHITECTURE.md §3.1) but that
  Planner integration itself hasn't landed; this phase ships the engine,
  not its first caller.
