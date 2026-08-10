import httpx
import pytest

from jarvis.brain.tools import ToolInvocationStatus, ToolRegistry
from jarvis.core.exceptions import PermissionDeniedError, ValidationError
from jarvis.security import InMemoryAuditLog, PermissionEngine, Role
from jarvis.web.agent import WebAgent
from jarvis.web.search import SearchResult
from jarvis.web.tools import register_web_tools


class _FakeSearchProvider:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        return self._results[:max_results]


def _client_with_html(html: str) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.fixture
def registry() -> ToolRegistry:
    engine = PermissionEngine()
    audit_log = InMemoryAuditLog()
    registry = ToolRegistry(engine, audit_log)
    web_agent = WebAgent(
        _client_with_html("<html><head><title>T</title></head><body>hi</body></html>"),
        search_provider=_FakeSearchProvider(
            [SearchResult(title="Result", url="https://x", snippet="snip")]
        ),
    )
    register_web_tools(registry, web_agent=web_agent)
    return registry


def test_web_tools_registered(registry: ToolRegistry) -> None:
    names = {tool.name for tool in registry.list_tools()}
    assert names == {"web_search", "web_fetch"}


@pytest.mark.asyncio
async def test_web_search_tool_returns_results(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="web_search",
        arguments={"query": "jarvis ai"},
        role=Role.OPERATOR,
        session_id="s1",
        actor="research",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert isinstance(result.result, dict)
    assert result.result["results"] == [{"title": "Result", "url": "https://x", "snippet": "snip"}]


@pytest.mark.asyncio
async def test_web_fetch_tool_returns_page(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="web_fetch",
        arguments={"url": "https://example.com"},
        role=Role.OPERATOR,
        session_id="s1",
        actor="research",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert isinstance(result.result, dict)
    assert result.result["title"] == "T"


@pytest.mark.asyncio
async def test_guest_denied_web_tools(registry: ToolRegistry) -> None:
    with pytest.raises(PermissionDeniedError):
        await registry.invoke(
            name="web_search",
            arguments={"query": "x"},
            role=Role.GUEST,
            session_id="s1",
            actor="research",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_web_search_rejects_non_string_query(registry: ToolRegistry) -> None:
    with pytest.raises(ValidationError):
        await registry.invoke(
            name="web_search",
            arguments={"query": 123},
            role=Role.OPERATOR,
            session_id="s1",
            actor="research",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_web_fetch_rejects_non_string_url(registry: ToolRegistry) -> None:
    with pytest.raises(ValidationError):
        await registry.invoke(
            name="web_fetch",
            arguments={"url": 123},
            role=Role.OPERATOR,
            session_id="s1",
            actor="research",
            correlation_id="c1",
        )
