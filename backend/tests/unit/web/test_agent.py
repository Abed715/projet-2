import httpx
import pytest

from jarvis.core.exceptions import ValidationError
from jarvis.web.agent import WebAgent
from jarvis.web.search import SearchResult


class _FakeSearchProvider:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results
        self.received_query: str | None = None

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        self.received_query = query
        return self._results[:max_results]


def _client_with_html(html: str, *, status_code: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text=html)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_fetch_returns_parsed_page() -> None:
    html = "<html><head><title>Hi</title></head><body><p>content</p></body></html>"
    client = _client_with_html(html)
    agent = WebAgent(client, search_provider=_FakeSearchProvider([]))

    page = await agent.fetch("https://example.com/page")

    assert page.title == "Hi"
    assert "content" in page.text
    assert page.status_code == 200


@pytest.mark.asyncio
async def test_fetch_truncates_long_text() -> None:
    long_paragraph = "word " * 10_000
    html = f"<html><body><p>{long_paragraph}</p></body></html>"
    client = _client_with_html(html)
    agent = WebAgent(client, search_provider=_FakeSearchProvider([]))

    page = await agent.fetch("https://example.com/big")

    assert len(page.text) <= 20_000


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/secret",
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.5/internal",
        "ftp://example.com/file",
    ],
)
@pytest.mark.asyncio
async def test_fetch_rejects_disallowed_urls(url: str) -> None:
    client = _client_with_html("<html></html>")
    agent = WebAgent(client, search_provider=_FakeSearchProvider([]))

    with pytest.raises(ValidationError):
        await agent.fetch(url)


@pytest.mark.asyncio
async def test_fetch_allows_ordinary_https_url() -> None:
    client = _client_with_html("<html><body>ok</body></html>")
    agent = WebAgent(client, search_provider=_FakeSearchProvider([]))

    page = await agent.fetch("https://example.com/")

    assert page.status_code == 200


@pytest.mark.asyncio
async def test_search_delegates_to_provider() -> None:
    results = [SearchResult(title="T", url="https://x", snippet="S")]
    provider = _FakeSearchProvider(results)
    agent = WebAgent(_client_with_html(""), search_provider=provider)

    found = await agent.search("query", max_results=3)

    assert found == results
    assert provider.received_query == "query"
