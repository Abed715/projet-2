"""Web research primitives: fetch a URL and extract text/tables, or search
and get back result snippets. Powered by an injected `httpx.AsyncClient` /
`SearchProvider` so tests run against `httpx.MockTransport` and a fake
provider — no real network calls.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from jarvis.core.exceptions import ValidationError
from jarvis.web.parsing import parse_html
from jarvis.web.search import SearchProvider, SearchResult

_MAX_FETCH_CHARS = 20_000
_DISALLOWED_HOSTS = {"localhost"}


def create_http_client(*, timeout_seconds: float = 15.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True)


def _is_disallowed_host(host: str) -> bool:
    if host in _DISALLOWED_HOSTS:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
    )


def _validate_fetch_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"unsupported URL scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise ValidationError(f"URL has no hostname: {url!r}")
    if _is_disallowed_host(parsed.hostname):
        raise ValidationError(f"fetching {parsed.hostname!r} is not permitted")


@dataclass(frozen=True, slots=True)
class FetchedPage:
    url: str
    status_code: int
    title: str
    text: str
    tables: list[list[list[str]]]


class WebAgent:
    """Research primitives: `fetch` a page, `search` the web.

    A best-effort SSRF guard on `fetch` rejects literal loopback/private-IP
    /localhost URLs; it cannot prevent DNS-rebinding attacks against a
    domain that resolves to a private address only at request time — that
    needs network-level egress control, out of scope for this module.
    """

    def __init__(self, client: httpx.AsyncClient, *, search_provider: SearchProvider) -> None:
        self._client = client
        self._search_provider = search_provider

    async def fetch(self, url: str) -> FetchedPage:
        _validate_fetch_url(url)
        response = await self._client.get(url)
        parsed = parse_html(response.text)
        return FetchedPage(
            url=str(response.url),
            status_code=response.status_code,
            title=parsed.title,
            text=parsed.text[:_MAX_FETCH_CHARS],
            tables=parsed.tables,
        )

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        return await self._search_provider.search(query, max_results=max_results)
