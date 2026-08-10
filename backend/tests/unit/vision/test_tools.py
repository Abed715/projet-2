import base64
import io

import pytest
from PIL import Image

from jarvis.brain.tools import ToolInvocationStatus, ToolRegistry
from jarvis.core.exceptions import ValidationError
from jarvis.security import InMemoryAuditLog, PermissionEngine, Role
from jarvis.vision.image_analysis import ImageAnalysisService
from jarvis.vision.ocr import OcrService
from jarvis.vision.screen_capture import ScreenCaptureService
from jarvis.vision.tools import register_vision_tools
from jarvis.vision.window_detection import WindowDetectionService, WindowInfo


class _FakeScreenCaptureBackend:
    def capture(self) -> bytes:
        return b"fake-png-bytes"


class _FakeWindowDetectionBackend:
    def list_windows(self) -> list[WindowInfo]:
        return [WindowInfo(window_id="0x1", title="Terminal")]


def _solid_color_png_base64() -> str:
    image = Image.new("RGB", (10, 10), color=(1, 2, 3))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


@pytest.fixture
def permission_engine() -> PermissionEngine:
    return PermissionEngine()


@pytest.fixture
def registry(permission_engine: PermissionEngine) -> ToolRegistry:
    audit_log = InMemoryAuditLog()
    registry = ToolRegistry(permission_engine, audit_log)
    register_vision_tools(
        registry,
        ocr=OcrService(),
        image_analysis=ImageAnalysisService(),
        screen_capture=ScreenCaptureService(_FakeScreenCaptureBackend()),
        window_detection=WindowDetectionService(_FakeWindowDetectionBackend()),
    )
    return registry


def test_all_tools_registered(registry: ToolRegistry) -> None:
    names = {tool.name for tool in registry.list_tools()}
    assert names == {"extract_text", "analyze_image", "capture_screen", "list_windows"}


@pytest.mark.asyncio
async def test_analyze_image_is_safe(registry: ToolRegistry) -> None:
    result = await registry.invoke(
        name="analyze_image",
        arguments={"image_base64": _solid_color_png_base64()},
        role=Role.GUEST,
        session_id="s1",
        actor="vision",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert isinstance(result.result, dict)
    assert result.result["average_color"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_analyze_image_rejects_non_string_input(registry: ToolRegistry) -> None:
    with pytest.raises(ValidationError):
        await registry.invoke(
            name="analyze_image",
            arguments={"image_base64": 123},
            role=Role.GUEST,
            session_id="s1",
            actor="vision",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_analyze_image_rejects_invalid_base64(registry: ToolRegistry) -> None:
    with pytest.raises(ValidationError):
        await registry.invoke(
            name="analyze_image",
            arguments={"image_base64": "not base64!!"},
            role=Role.GUEST,
            session_id="s1",
            actor="vision",
            correlation_id="c1",
        )


@pytest.mark.asyncio
async def test_capture_screen_is_sensitive_but_allowed_for_operator(
    registry: ToolRegistry,
) -> None:
    result = await registry.invoke(
        name="capture_screen",
        arguments={},
        role=Role.OPERATOR,
        session_id="s1",
        actor="vision",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert result.result == {"image_base64": "ZmFrZS1wbmctYnl0ZXM="}


@pytest.mark.asyncio
async def test_list_windows_after_grant(
    registry: ToolRegistry, permission_engine: PermissionEngine
) -> None:
    permission_engine.grant_for_session("s1", "list_windows")

    result = await registry.invoke(
        name="list_windows",
        arguments={},
        role=Role.OWNER,
        session_id="s1",
        actor="vision",
        correlation_id="c1",
    )

    assert result.status is ToolInvocationStatus.OK
    assert result.result == {"windows": [{"id": "0x1", "title": "Terminal"}]}
