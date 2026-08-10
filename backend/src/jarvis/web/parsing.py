"""Minimal, dependency-free HTML → text/table extraction, using only the
stdlib `html.parser`. Enough for research-agent consumption (title, body
text, tables) without adding a heavy HTML parsing dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

_SKIP_TAGS = {"script", "style", "noscript", "template"}
_BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}


@dataclass(frozen=True, slots=True)
class ParsedPage:
    title: str
    text: str
    tables: list[list[list[str]]]


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self._tables: list[list[list[str]]] = []
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "table":
            self._current_table = []
        elif tag == "tr" and self._current_table is not None:
            self._current_row = []
        elif tag in ("td", "th") and self._current_row is not None:
            self._current_cell = []
        elif tag in _BLOCK_TAGS:
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "title":
            self._in_title = False
        elif tag in ("td", "th") and self._current_row is not None:
            if self._current_cell is not None:
                self._current_row.append("".join(self._current_cell).strip())
            self._current_cell = None
        elif tag == "tr" and self._current_table is not None:
            if self._current_row is not None:
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._current_table is not None:
            self._tables.append(self._current_table)
            self._current_table = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
        if self._current_cell is not None:
            self._current_cell.append(data)
        else:
            self._text_parts.append(data)

    def result(self) -> ParsedPage:
        title = "".join(self._title_parts).strip()
        raw_text = "".join(self._text_parts)
        lines = [line.strip() for line in raw_text.splitlines()]
        text = "\n".join(line for line in lines if line)
        return ParsedPage(title=title, text=text, tables=self._tables)


def parse_html(html: str) -> ParsedPage:
    parser = _PageParser()
    parser.feed(html)
    parser.close()
    return parser.result()
