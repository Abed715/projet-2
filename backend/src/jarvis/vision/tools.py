"""Registers `vision`'s OCR/image-analysis/screen-capture/window-detection
capabilities as tools in `brain`'s `ToolRegistry`, each tagged with the
risk level `security.rbac` enforces before it runs.
"""

from __future__ import annotations

import base64

from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import ValidationError
from jarvis.security import RiskLevel
from jarvis.vision.image_analysis import ImageAnalysisService
from jarvis.vision.ocr import OcrService
from jarvis.vision.screen_capture import ScreenCaptureService
from jarvis.vision.window_detection import WindowDetectionService


def _require_image_bytes(arguments: dict[str, object]) -> bytes:
    value = arguments.get("image_base64")
    if not isinstance(value, str):
        raise ValidationError("'image_base64' must be a base64-encoded string")
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValidationError("'image_base64' is not valid base64") from exc


def register_vision_tools(
    registry: ToolRegistry,
    *,
    ocr: OcrService,
    image_analysis: ImageAnalysisService,
    screen_capture: ScreenCaptureService,
    window_detection: WindowDetectionService,
) -> None:
    async def extract_text(arguments: dict[str, object]) -> object:
        image_bytes = _require_image_bytes(arguments)
        return {"text": await ocr.extract_text(image_bytes)}

    async def analyze_image(arguments: dict[str, object]) -> object:
        image_bytes = _require_image_bytes(arguments)
        summary = await image_analysis.analyze(image_bytes)
        return {
            "width": summary.width,
            "height": summary.height,
            "format": summary.format,
            "average_color": list(summary.average_color),
        }

    async def capture_screen(arguments: dict[str, object]) -> object:
        png_bytes = await screen_capture.capture()
        return {"image_base64": base64.b64encode(png_bytes).decode("ascii")}

    async def list_windows(arguments: dict[str, object]) -> object:
        windows = await window_detection.list_windows()
        return {"windows": [{"id": w.window_id, "title": w.title} for w in windows]}

    registry.register(
        ToolSpec(
            name="extract_text",
            description="Run OCR on an image and return the recognized text.",
            risk_level=RiskLevel.SAFE,
            handler=extract_text,
            input_schema={
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Base64-encoded image"}
                },
                "required": ["image_base64"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="analyze_image",
            description="Get basic metadata (size, format, average color) for an image.",
            risk_level=RiskLevel.SAFE,
            handler=analyze_image,
            input_schema={
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Base64-encoded image"}
                },
                "required": ["image_base64"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="capture_screen",
            description="Take a screenshot of the primary monitor.",
            risk_level=RiskLevel.SENSITIVE,
            handler=capture_screen,
            input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="list_windows",
            description="List currently open windows (id and title).",
            risk_level=RiskLevel.SENSITIVE,
            handler=list_windows,
            input_schema={"type": "object", "properties": {}},
        )
    )
