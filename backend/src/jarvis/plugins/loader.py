"""PluginLoader: a small registry of `Plugin` instances. Loading a plugin
means calling its `register_tools` once against a shared `brain.
ToolRegistry` — there is no separate plugin sandbox or process boundary
here; the existing `ToolRegistry` + `security` path already mediates every
call a plugin's tools make. See `plugins/README.md`.
"""

from __future__ import annotations

from jarvis.brain.tools import ToolRegistry
from jarvis.core.exceptions import ConfigurationError
from jarvis.plugins.base import Plugin
from jarvis.plugins.manifest import PluginManifest


class PluginLoader:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        name = plugin.manifest.name
        if name in self._plugins:
            raise ConfigurationError(f"a plugin named {name!r} is already registered")
        self._plugins[name] = plugin

    def load_all(self, registry: ToolRegistry) -> list[PluginManifest]:
        """Register every plugin's tools into `registry`, in registration
        order. Returns the manifests actually loaded, for logging/display.
        """
        manifests = []
        for plugin in self._plugins.values():
            plugin.register_tools(registry)
            manifests.append(plugin.manifest)
        return manifests

    def list_plugins(self) -> list[PluginManifest]:
        return [plugin.manifest for plugin in self._plugins.values()]
