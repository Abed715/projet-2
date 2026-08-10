import httpx
import pytest

from jarvis.brain.tools import ToolInvocationStatus, ToolRegistry
from jarvis.core.exceptions import ConfigurationError, NotFoundError, ValidationError
from jarvis.plugins.builtin.github import GitHubPlugin
from jarvis.security import InMemoryAuditLog, PermissionEngine, Role

_REPO_JSON = {
    "full_name": "anthropics/claude-code",
    "description": "An agentic coding tool",
    "stargazers_count": 100,
    "forks_count": 10,
    "open_issues_count": 5,
    "html_url": "https://github.com/anthropics/claude-code",
}


def _client(status_code: int, json_body: object | None) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=json_body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry(PermissionEngine(), InMemoryAuditLog())


def test_manifest_fields() -> None:
    plugin = GitHubPlugin(_client(200, _REPO_JSON))

    assert plugin.manifest.name == "github"
    assert plugin.manifest.version
    assert plugin.manifest.description


def test_registers_one_tool(registry: ToolRegistry) -> None:
    plugin = GitHubPlugin(_client(200, _REPO_JSON))

    plugin.register_tools(registry)

    assert {t.name for t in registry.list_tools()} == {"github_repo_info"}


@pytest.mark.asyncio
async def test_repo_info_returns_expected_fields(registry: ToolRegistry) -> None:
    plugin = GitHubPlugin(_client(200, _REPO_JSON))
    plugin.register_tools(registry)

    result = await registry.invoke(
        name="github_repo_info",
        arguments={"owner": "anthropics", "repo": "claude-code"},
        role=Role.GUEST,
        session_id="s1",
        actor="plugin",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert result.result == {
        "full_name": "anthropics/claude-code",
        "description": "An agentic coding tool",
        "stars": 100,
        "forks": 10,
        "open_issues": 5,
        "url": "https://github.com/anthropics/claude-code",
    }


@pytest.mark.asyncio
async def test_missing_repo_raises_not_found(registry: ToolRegistry) -> None:
    plugin = GitHubPlugin(_client(404, {"message": "Not Found"}))
    plugin.register_tools(registry)

    with pytest.raises(NotFoundError):
        await registry.invoke(
            name="github_repo_info",
            arguments={"owner": "nobody", "repo": "nothing"},
            role=Role.GUEST,
            session_id="s1",
            actor="plugin",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_unexpected_status_raises_configuration_error(registry: ToolRegistry) -> None:
    plugin = GitHubPlugin(_client(503, {"message": "unavailable"}))
    plugin.register_tools(registry)

    with pytest.raises(ConfigurationError):
        await registry.invoke(
            name="github_repo_info",
            arguments={"owner": "a", "repo": "b"},
            role=Role.GUEST,
            session_id="s1",
            actor="plugin",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_missing_owner_raises_validation_error(registry: ToolRegistry) -> None:
    plugin = GitHubPlugin(_client(200, _REPO_JSON))
    plugin.register_tools(registry)

    with pytest.raises(ValidationError):
        await registry.invoke(
            name="github_repo_info",
            arguments={"repo": "b"},
            role=Role.GUEST,
            session_id="s1",
            actor="plugin",
            correlation_id="c1",
        )
