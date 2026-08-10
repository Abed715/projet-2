import json
import logging

from jarvis.core.logging import (
    configure_logging,
    get_correlation_id,
    get_logger,
    reset_correlation_id,
    set_correlation_id,
)


def test_correlation_id_defaults_to_none() -> None:
    assert get_correlation_id() is None


def test_set_and_reset_correlation_id() -> None:
    token = set_correlation_id("abc-123")
    try:
        assert get_correlation_id() == "abc-123"
    finally:
        reset_correlation_id(token)

    assert get_correlation_id() is None


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("jarvis.test.module")

    assert logger.name == "jarvis.test.module"


def test_json_formatter_emits_valid_json(capsys) -> None:  # type: ignore[no-untyped-def]
    configure_logging(level="INFO", json_format=True)
    logger = get_logger("jarvis.test.json")

    token = set_correlation_id("req-42")
    try:
        logger.info("hello world")
    finally:
        reset_correlation_id(token)

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["message"] == "hello world"
    assert payload["correlation_id"] == "req-42"
    assert payload["level"] == "INFO"

    # restore human-readable format for any subsequent tests in this process
    configure_logging(level="INFO", json_format=False)


def test_configure_logging_is_idempotent() -> None:
    configure_logging(level="DEBUG")
    configure_logging(level="DEBUG")

    root = logging.getLogger()
    assert len(root.handlers) == 1
