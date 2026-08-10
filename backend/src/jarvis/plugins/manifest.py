"""Plugin manifest — the declarative metadata a plugin exposes: what it
is, and who wrote it. Loading a plugin never reads this metadata to grant
extra trust; every tool a plugin registers still goes through the same
`security.PermissionEngine`/`AuditLog` path as any other tool — see
`plugins/README.md`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PluginManifest:
    name: str
    version: str
    description: str
    author: str = "unknown"
