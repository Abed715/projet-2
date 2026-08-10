"""jarvis.web — web research: fetch, search, and their tool registrations.

See README.md for the full public interface and design notes.
"""

from jarvis.web.agent import FetchedPage, WebAgent, create_http_client
from jarvis.web.parsing import ParsedPage, parse_html
from jarvis.web.search import DuckDuckGoSearchProvider, SearchProvider, SearchResult
from jarvis.web.tools import register_web_tools

__all__ = [
    "FetchedPage",
    "WebAgent",
    "create_http_client",
    "ParsedPage",
    "parse_html",
    "DuckDuckGoSearchProvider",
    "SearchProvider",
    "SearchResult",
    "register_web_tools",
]
