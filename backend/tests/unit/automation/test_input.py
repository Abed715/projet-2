import pytest

from jarvis.automation.input import InputService, PyAutoGuiInputBackend
from jarvis.core.exceptions import ConfigurationError


class _FakeInputBackend:
    def __init__(self) -> None:
        self.moved: tuple[int, int] | None = None
        self.clicked = False
        self.typed: str | None = None
        self.pressed: str | None = None

    def move_mouse(self, x: int, y: int) -> None:
        self.moved = (x, y)

    def click(self) -> None:
        self.clicked = True

    def type_text(self, text: str) -> None:
        self.typed = text

    def press_key(self, key: str) -> None:
        self.pressed = key


@pytest.mark.asyncio
async def test_input_service_delegates_to_backend() -> None:
    backend = _FakeInputBackend()
    service = InputService(backend)

    await service.move_mouse(10, 20)
    await service.click()
    await service.type_text("hello")
    await service.press_key("enter")

    assert backend.moved == (10, 20)
    assert backend.clicked is True
    assert backend.typed == "hello"
    assert backend.pressed == "enter"


def test_pyautogui_backend_raises_configuration_error_without_display() -> None:
    # This sandbox has no $DISPLAY, so pyautogui fails at import time — the
    # constructor must translate that into a ConfigurationError rather than
    # letting pyautogui's own KeyError escape.
    with pytest.raises(ConfigurationError):
        PyAutoGuiInputBackend()
