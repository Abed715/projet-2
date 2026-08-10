"""Web search: one interface, one implementation today.

Mirrors `brain.providers.LLMProvider`'s pattern — a `SearchProvider`
protocol so a paid search API (Bing, Brave, Serper, ...) can be swapped in
later without touching `WebAgent` or the tool registration.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Protocol

import httpx

from jarvis.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(Protocol):
    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]: ...


class _SearchResultParser(HTMLParser):
    """Parses DuckDuckGo's HTML results page.

    Targets `<a class="result__a">` (title + link) and
    `<a class="result__snippet">` (summary) — the shape of the plain
    `html.duckduckgo.com/html/` endpoint, not the JS-heavy main site.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[SearchResult] = []
        self._current_url: str | None = None
        self._current_title_parts: list[str] = []
        self._current_snippet_parts: list[str] = []
        self._in_title_link = False
        self._in_snippet = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()
        if tag == "a" and "result__a" in classes:
            self._in_title_link = True
            self._current_url = attrs_dict.get("href")
            self._current_title_parts = []
        elif tag in ("a", "div", "span") and "result__snippet" in classes:
            self._in_snippet = True
            self._current_snippet_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_title_link:
            self._in_title_link = False
        elif self._in_snippet and tag in ("a", "div", "span"):
            self._in_snippet = False
            if self._current_url:
                self.results.append(
                    SearchResult(
                        title="".join(self._current_title_parts).strip(),
                        url=self._current_url,
                        snippet="".join(self._current_snippet_parts).strip(),
                    )
                )
                self._current_url = None

    def handle_data(self, data: str) -> None:
        if self._in_title_link:
            self._current_title_parts.append(data)
        elif self._in_snippet:
            self._current_snippet_parts.append(data)


def _parse_duckduckgo_results(html: str, *, max_results: int) -> list[SearchResult]:
    parser = _SearchResultParser()
    parser.feed(html)
    parser.close()
    return parser.results[:max_results]


class DuckDuckGoSearchProvider:
    """Searches via DuckDuckGo's HTML endpoint (no API key required).

    Best-effort: DuckDuckGo's HTML structure isn't a stable contract, so
    this can break if they change it. Swap in a paid provider behind the
    same `SearchProvider` protocol when reliability matters more than
    "free, no signup."
    """

    _ENDPOINT = "https://html.duckduckgo.com/html/"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        if not query.strip():
            raise ValidationError("search query must not be empty")
        response = await self._client.get(self._ENDPOINT, params={"q": query})
        return _parse_duckduckgo_results(response.text, max_results=max_results)
