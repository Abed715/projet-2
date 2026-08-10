# jarvis.vision

**Status:** implemented (Phase 4). Depends on `jarvis.core`, `jarvis.security`
(risk levels only), and `jarvis.brain` (to register tools into
`ToolRegistry`).

## Public interface

```python
from jarvis.vision import (
    OcrService,
    ImageAnalysisService, ImageSummary,
    ScreenCaptureService, ScreenCaptureBackend, MssScreenCaptureBackend,
    WindowDetectionService, WindowDetectionBackend, WindowInfo, WmctrlWindowDetectionBackend,
    register_vision_tools,
)
```

- **`OcrService`** — `extract_text(image_bytes) -> str`, via `pytesseract` +
  Pillow. Headless-safe (no display required), so this talks to
  `pytesseract` directly rather than through a backend Protocol — unlike
  the rest of `vision`.
- **`ImageAnalysisService`** — `analyze(image_bytes) -> ImageSummary`
  (width, height, format, average RGB color), via Pillow. Also
  headless-safe.
- **`ScreenCaptureService(backend)`** — `capture() -> bytes` (PNG) over a
  `ScreenCaptureBackend` Protocol. `MssScreenCaptureBackend` is the real
  implementation.
- **`WindowDetectionService(backend)`** — `list_windows() -> list[WindowInfo]`
  over a `WindowDetectionBackend` Protocol. `WmctrlWindowDetectionBackend`
  is the real implementation (X11/`wmctrl` only for now).
- **`register_vision_tools(registry, *, ocr, image_analysis, screen_capture,
  window_detection)`** — registers `extract_text`/`analyze_image` (`SAFE`
  — read-only, no OS side effects) and `capture_screen`/`list_windows`
  (`SENSITIVE` — read the user's screen/window state). Images cross the
  tool boundary as base64 strings (`image_base64`), matching how Claude's
  tool-use JSON payloads carry binary data.

## Design notes: headless environments

Same empirical-verification approach as `automation/README.md`:

- **`pytesseract`/Pillow** were verified to work fully headlessly, given the
  `tesseract-ocr` system package (installed in CI — see
  `.github/workflows/backend-ci.yml`). `OcrService` calls them directly.
- **`mss`** imports safely at module scope, but constructing `mss.mss()`
  itself opens a connection to the display server and raises headlessly.
  `MssScreenCaptureBackend.capture()` defers both the import and the
  construction into the method body (not `__init__`), and translates any
  failure into `ConfigurationError`.
- **`wmctrl`** may simply not be installed, or there may be no X11 session
  to query. `WmctrlWindowDetectionBackend` checks `shutil.which("wmctrl")`
  up front, same pattern as `automation`'s `notify-send` check.

Every backend is still swappable via its Protocol for testing: unit tests
inject fakes, never the real display-touching implementations. OCR and
image analysis are exercised in tests with real, synthetically generated
images (rendered text, solid colors) — no fakes needed there since they're
headless-safe.

## Known limitations / deferred

- **Object detection** (bounding boxes, scene labels) is not implemented —
  no CV model dependency has been added yet; `ARCHITECTURE.md`'s vision
  scope still lists it as a future capability.
- **Webcam / live camera input** is not implemented — deferred until a
  concrete use case needs it (OpenCV's `VideoCapture` also has its own
  headless/device-availability constraints to design around).
- **`WmctrlWindowDetectionBackend`** is X11/`wmctrl` only. Wayland and
  macOS/Windows window enumeration are deferred until there's a target
  platform to test against — same reasoning as
  `automation.DesktopNotificationBackend`.
- **`MssScreenCaptureBackend`** captures the primary monitor only;
  multi-monitor selection is not exposed yet.
