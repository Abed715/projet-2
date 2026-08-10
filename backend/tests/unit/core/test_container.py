import pytest

from jarvis.core.container import Container
from jarvis.core.exceptions import ConfigurationError


class _ServiceA:
    pass


class _ServiceB:
    pass


def test_resolve_raises_when_unregistered() -> None:
    container = Container()

    with pytest.raises(ConfigurationError):
        container.resolve(_ServiceA)


def test_register_instance_returns_same_object() -> None:
    container = Container()
    instance = _ServiceA()

    container.register_instance(_ServiceA, instance)

    assert container.resolve(_ServiceA) is instance
    assert container.resolve(_ServiceA) is instance  # still the same singleton


def test_register_factory_is_called_each_resolve() -> None:
    container = Container()
    calls = {"count": 0}

    def factory() -> _ServiceB:
        calls["count"] += 1
        return _ServiceB()

    container.register_factory(_ServiceB, factory)

    first = container.resolve(_ServiceB)
    second = container.resolve(_ServiceB)

    assert first is not second
    assert calls["count"] == 2


def test_has_reflects_registration_state() -> None:
    container = Container()
    assert container.has(_ServiceA) is False

    container.register_instance(_ServiceA, _ServiceA())
    assert container.has(_ServiceA) is True
