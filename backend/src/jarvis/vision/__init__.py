"""jarvis.vision — screen/image understanding: OCR, basic image analysis,
screen capture, and window detection, plus their tool registrations.

See README.md for the full public interface and design notes.
"""

from jarvis.vision.image_analysis import ImageAnalysisService, ImageSummary
from jarvis.vision.ocr import OcrService
from jarvis.vision.screen_capture import (
    MssScreenCaptureBackend,
    ScreenCaptureBackend,
    ScreenCaptureService,
)
from jarvis.vision.tools import register_vision_tools
from jarvis.vision.window_detection import (
    WindowDetectionBackend,
    WindowDetectionService,
    WindowInfo,
    WmctrlWindowDetectionBackend,
)

__all__ = [
    "ImageAnalysisService",
    "ImageSummary",
    "MssScreenCaptureBackend",
    "OcrService",
    "ScreenCaptureBackend",
    "ScreenCaptureService",
    "WindowDetectionBackend",
    "WindowDetectionService",
    "WindowInfo",
    "WmctrlWindowDetectionBackend",
    "register_vision_tools",
]
