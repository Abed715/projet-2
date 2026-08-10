# jarvis.security

**Status:** implemented (Phase 1).

Every dangerous action in the system is mediated here. Depends only on
`jarvis.core`; no domain module (`memory`, `automation`, ...) may bypass it.

## Public interface

```python
from jarvis.security import (
    Role, RiskLevel, role_permits,               # RBAC
    PermissionEngine, PermissionDecision, PermissionResult,  # permission engine
    AuditLog, AuditEntry, InMemoryAuditLog, SqlAuditLog, redact,  # audit log
    SecretsVault,                                 # encryption at rest
)
```

- **`Role` / `RiskLevel` / `role_permits`** — the coarse RBAC gate. Three
  roles (`guest`, `operator`, `owner`); three risk levels a tool can be
  tagged with (`safe`, `sensitive`, `dangerous`). `role_permits(role,
  risk_level)` answers "can this role reach this risk level at all,"
  independent of confirmation.
- **`PermissionEngine`** — the actual enforcement point every tool call goes
  through. Tools register a risk level once; `evaluate(role=..., tool_name=...,
  session_id=...)` returns `ALLOW`, `REQUIRES_CONFIRMATION`, or `DENY`.
  `DANGEROUS` tools require confirmation unless the session has previously
  granted an "always allow" for that specific tool
  (`grant_for_session`/`revoke_for_session`).
- **`AuditLog`** — a `Protocol` with two implementations: `InMemoryAuditLog`
  (dev/tests) and `SqlAuditLog` (Postgres in production, SQLite in tests,
  both via `jarvis.core.db.Database`). `redact()` is a best-effort helper
  that masks parameter values whose key looks like a credential before
  they're written.
- **`SecretsVault`** — Fernet encryption keyed off `Settings.secret_key`
  (SHA-256-derived, so operators manage one secret, not two). Used to store
  plugin credentials and provider API keys at rest.

## Design notes

- The permission engine is deliberately ignorant of *what* a tool does —
  only its registered risk level. Risk tagging happens where tools are
  defined (the tool registry in `brain`, Phase 2); this module only
  enforces the policy.
- `SqlAuditLog` and future Postgres-backed stores (`memory`'s episodic
  store) share `jarvis.core.db.Base`'s metadata — a single `create_all()`
  (dev) or Alembic migration (production) covers every module's tables.
- Not yet implemented: the **Sandbox Executor** (subprocess isolation for
  shell/plugin execution) — it lands with `jarvis.system` in Phase 3, since
  it has nothing to sandbox until then.
