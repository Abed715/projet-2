"""Plugin protocol: a manifest plus a `register_tools` hook that adds the
plugin's capabilities into a `brain.ToolRegistry` — the same registry
`system`/`web`/`automation`/`vision` register into, so plugin tools get
identical permission checks, audit logging, and confirmation semantics
with no plugin-specific plumbing. See `plugins/README.md`.
"""

from __future__ import annotations

from typing import Protocol

from jarvis.brain.tools import ToolRegistry
from jarvis.plugins.manifest import PluginManifest


class Plugin(Protocol):
    @property
    def manifest(self) -> PluginManifest: ...

    def register_tools(self, registry: ToolRegistry) -> None: ...
