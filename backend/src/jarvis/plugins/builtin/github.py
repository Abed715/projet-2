"""Reference plugin: public GitHub repository lookups. Exists to prove the
plugin mechanism end to end (manifest + `register_tools` -> a real tool
running through the normal permission/audit path), not as a full GitHub
integration — see `plugins/README.md` for what's deliberately out of
scope (auth, issues/PRs, rate-limit handling beyond surfacing the error).

Follows `web.agent.WebAgent`'s pattern: an injected `httpx.AsyncClient` so
tests run against `httpx.MockTransport`, no real network calls.
"""

from __future__ import annotations

import httpx

from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import ConfigurationError, NotFoundError, ValidationError
from jarvis.plugins.base import Plugin
from jarvis.plugins.manifest import PluginManifest
from jarvis.security import RiskLevel

_MANIFEST = PluginManifest(
    name="github",
    version="0.1.0",
    description="Look up public GitHub repository info.",
    author="jarvis",
)


def _require_str(arguments: dict[str, object], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{key!r} must be a non-empty string")
    return value


class GitHubPlugin:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @property
    def manifest(self) -> PluginManifest:
        return _MANIFEST

    def register_tools(self, registry: ToolRegistry) -> None:
        async def github_repo_info(arguments: dict[str, object]) -> object:
            owner = _require_str(arguments, "owner")
            repo = _require_str(arguments, "repo")

            response = await self._client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if response.status_code == 404:
                raise NotFoundError(f"no repository {owner}/{repo}")
            if response.status_code != 200:
                raise ConfigurationError(
                    f"GitHub API returned {response.status_code} for {owner}/{repo}"
                )

            data = response.json()
            return {
                "full_name": data["full_name"],
                "description": data.get("description"),
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "open_issues": data["open_issues_count"],
                "url": data["html_url"],
            }

        registry.register(
            ToolSpec(
                name="github_repo_info",
                description="Look up public info (stars, forks, description) for a GitHub repo.",
                risk_level=RiskLevel.SAFE,
                handler=github_repo_info,
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"},
                    },
                    "required": ["owner", "repo"],
                },
            )
        )


_github_plugin_satisfies_protocol: type[Plugin] = GitHubPlugin
