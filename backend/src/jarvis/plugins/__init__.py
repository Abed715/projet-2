"""jarvis.plugins — manifest spec, loader, and built-in reference plugins.
Plugin tools run through the exact same `brain.ToolRegistry` /
`security.PermissionEngine` / `security.AuditLog` path as every other
module's tools — see README.md for why that's the whole design.
"""

from jarvis.plugins.base import Plugin
from jarvis.plugins.builtin.github import GitHubPlugin
from jarvis.plugins.loader import PluginLoader
from jarvis.plugins.manifest import PluginManifest

__all__ = [
    "GitHubPlugin",
    "Plugin",
    "PluginLoader",
    "PluginManifest",
]
