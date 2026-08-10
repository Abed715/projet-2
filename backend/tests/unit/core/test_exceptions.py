import pytest

from jarvis.core.exceptions import (
    ConfigurationError,
    JarvisError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


@pytest.mark.parametrize(
    "error_cls",
    [ConfigurationError, NotFoundError, ValidationError, PermissionDeniedError],
)
def test_all_domain_errors_are_jarvis_errors(error_cls: type[JarvisError]) -> None:
    assert issubclass(error_cls, JarvisError)


def test_message_and_details_are_preserved() -> None:
    error = NotFoundError("user not found", details={"user_id": "abc"})

    assert error.message == "user not found"
    assert error.details == {"user_id": "abc"}
    assert str(error) == "user not found"


def test_details_default_to_empty_dict() -> None:
    error = ValidationError("bad input")

    assert error.details == {}
