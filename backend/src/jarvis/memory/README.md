# jarvis.memory

**Status:** implemented (Phase 1) — short-term, episodic, and semantic
layers. Depends only on `jarvis.core`.

## Public interface

```python
from jarvis.memory import (
    ShortTermMemory, Turn, RedisLike,             # short-term (Redis)
    EpisodicStore, Episode, EpisodeKind,           # episodic (Postgres)
    SemanticMemory, SemanticMatch,                 # semantic (ChromaDB)
    create_ephemeral_client, create_http_client,
)
```

- **`ShortTermMemory`** — the active conversation buffer. Appends `Turn`s to
  a per-session Redis list, trimmed to `max_turns` and TTL'd. Built against a
  `RedisLike` protocol (the subset of `redis.asyncio.Redis` it needs) so
  tests use `fakeredis` instead of a real server.
- **`EpisodicStore`** — durable, queryable memory: conversation history,
  task history, project history, user preferences — all modeled as
  `Episode`s tagged with an `EpisodeKind`, stored via
  `jarvis.core.db.Database` (Postgres in production, SQLite in tests). One
  table rather than one per kind: the kinds share the same shape (session,
  timestamp, arbitrary JSON content) and querying "everything for this
  session" is a common case worth keeping cheap.
- **`SemanticMemory`** — similarity search over a ChromaDB collection.
  **Does not generate embeddings itself** — callers (the Memory Agent, via
  `jarvis.brain`'s embedding provider in Phase 2) pass a precomputed
  `embedding: list[float]`. This keeps the module usable with no network
  access and no model download in tests; `create_ephemeral_client()` is an
  in-process Chroma instance for exactly that, `create_http_client()` points
  at the `chroma` service in `docker-compose.yml` for production.

## Design notes

- **Context compression** (ARCHITECTURE.md §6): summarizing aging
  short-term turns into a durable `Episode` before they're trimmed from
  Redis is the Memory Agent's responsibility, not this module's — `memory`
  only provides the storage primitives, `jarvis.agents` (Phase 2) owns the
  policy of *when* to summarize.
- **Knowledge graph**: deferred. The architecture calls for entities/edges
  extracted from conversations; it's naturally modeled as more `Episode`
  rows (`kind="relation"`, content `{subject, predicate, object}`) once
  there's an extraction step to populate it — no schema work needed ahead
  of that, so it isn't speculatively built now.
- Postgres-only features (JSONB indexing, `pgvector`) are deliberately not
  used yet so the same models test against SQLite without a running
  Postgres; revisit once semantic search needs to live in Postgres directly
  rather than ChromaDB.
