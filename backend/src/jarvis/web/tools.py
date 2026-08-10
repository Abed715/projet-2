"""Registers `web`'s research capabilities as tools in `brain`'s
`ToolRegistry`.
"""

from __future__ import annotations

from dataclasses import asdict

from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import ValidationError
from jarvis.security import RiskLevel
from jarvis.web.agent import WebAgent


def register_web_tools(registry: ToolRegistry, *, web_agent: WebAgent) -> None:
    async def web_search(arguments: dict[str, object]) -> object:
        query = arguments.get("query")
        if not isinstance(query, str):
            raise ValidationError("'query' must be a string")
        max_results = arguments.get("max_results", 5)
        if not isinstance(max_results, int):
            raise ValidationError("'max_results' must be an integer")
        results = await web_agent.search(query, max_results=max_results)
        return {"results": [asdict(result) for result in results]}

    async def web_fetch(arguments: dict[str, object]) -> object:
        url = arguments.get("url")
        if not isinstance(url, str):
            raise ValidationError("'url' must be a string")
        page = await web_agent.fetch(url)
        return {
            "url": page.url,
            "status_code": page.status_code,
            "title": page.title,
            "text": page.text,
            "tables": page.tables,
        }

    registry.register(
        ToolSpec(
            name="web_search",
            description="Search the web and return a list of {title, url, snippet} results.",
            risk_level=RiskLevel.SENSITIVE,
            handler=web_search,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return, default 5",
                    },
                },
                "required": ["query"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="web_fetch",
            description=(
                "Fetch a URL and extract its title, visible text, and any HTML tables."
            ),
            risk_level=RiskLevel.SENSITIVE,
            handler=web_fetch,
            input_schema={
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to fetch"}},
                "required": ["url"],
            },
        )
    )
