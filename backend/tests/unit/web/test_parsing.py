from jarvis.web.parsing import parse_html


def test_extracts_title() -> None:
    result = parse_html("<html><head><title>My Page</title></head><body></body></html>")

    assert result.title == "My Page"


def test_extracts_visible_text() -> None:
    html = "<html><body><p>Hello</p><p>World</p></body></html>"

    result = parse_html(html)

    assert "Hello" in result.text
    assert "World" in result.text


def test_skips_script_and_style_content() -> None:
    html = (
        "<html><body>"
        "<script>var x = 'should not appear';</script>"
        "<style>.x { color: red; }</style>"
        "<p>Visible text</p>"
        "</body></html>"
    )

    result = parse_html(html)

    assert "should not appear" not in result.text
    assert "color: red" not in result.text
    assert "Visible text" in result.text


def test_extracts_table_rows_and_cells() -> None:
    html = (
        "<table>"
        "<tr><th>Name</th><th>Age</th></tr>"
        "<tr><td>Alice</td><td>30</td></tr>"
        "</table>"
    )

    result = parse_html(html)

    assert result.tables == [[["Name", "Age"], ["Alice", "30"]]]


def test_multiple_tables_are_all_captured() -> None:
    html = "<table><tr><td>A</td></tr></table><table><tr><td>B</td></tr></table>"

    result = parse_html(html)

    assert result.tables == [[["A"]], [["B"]]]


def test_empty_html_produces_empty_result() -> None:
    result = parse_html("")

    assert result.title == ""
    assert result.text == ""
    assert result.tables == []


def test_no_title_tag_produces_empty_title() -> None:
    result = parse_html("<html><body><p>No title here</p></body></html>")

    assert result.title == ""
