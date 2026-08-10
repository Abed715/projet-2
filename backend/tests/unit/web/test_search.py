import httpx
import pytest

from jarvis.core.exceptions import ValidationError
from jarvis.web.search import DuckDuckGoSearchProvider

_SAMPLE_RESULTS_HTML = """
<html><body>
<div class="result">
  <a class="result__a" href="https://example.com/one">Example One</a>
  <a class="result__snippet">This is the first snippet.</a>
</div>
<div class="result">
  <a class="result__a" href="https://example.com/two">Example Two</a>
  <a class="result__snippet">This is the second snippet.</a>
</div>
</body></html>
"""


def _client_with_response(html: str) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport)


@pytest.mark.asyncio
async def test_search_parses_results() -> None:
    client = _client_with_response(_SAMPLE_RESULTS_HTML)
    provider = DuckDuckGoSearchProvider(client)

    results = await provider.search("test query")

    assert len(results) == 2
    assert results[0].title == "Example One"
    assert results[0].url == "https://example.com/one"
    assert results[0].snippet == "This is the first snippet."
    assert results[1].title == "Example Two"


@pytest.mark.asyncio
async def test_search_respects_max_results() -> None:
    client = _client_with_response(_SAMPLE_RESULTS_HTML)
    provider = DuckDuckGoSearchProvider(client)

    results = await provider.search("test query", max_results=1)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_rejects_empty_query() -> None:
    client = _client_with_response(_SAMPLE_RESULTS_HTML)
    provider = DuckDuckGoSearchProvider(client)

    with pytest.raises(ValidationError):
        await provider.search("   ")


@pytest.mark.asyncio
async def test_search_sends_query_as_param() -> None:
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, text=_SAMPLE_RESULTS_HTML)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = DuckDuckGoSearchProvider(client)

    await provider.search("hello world")

    assert captured["request"].url.params["q"] == "hello world"


@pytest.mark.asyncio
async def test_search_with_no_results_returns_empty_list() -> None:
    client = _client_with_response("<html><body>no results</body></html>")
    provider = DuckDuckGoSearchProvider(client)

    results = await provider.search("nothing found")

    assert results == []
