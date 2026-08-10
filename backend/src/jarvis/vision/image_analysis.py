"""Basic image metadata/analysis over Pillow — dimensions, format, and
average color. Headless-safe like `ocr.py`; deeper analysis (object
detection, scene understanding) is deferred, see `vision/README.md`.
"""

from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass

from PIL import Image

from jarvis.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ImageSummary:
    width: int
    height: int
    format: str
    average_color: tuple[int, int, int]


class ImageAnalysisService:
    async def analyze(self, image_bytes: bytes) -> ImageSummary:
        if not image_bytes:
            raise ValidationError("image_bytes must not be empty")

        def _run() -> ImageSummary:
            try:
                image = Image.open(io.BytesIO(image_bytes))
                image.load()
            except Exception as exc:
                raise ValidationError("could not decode image data") from exc

            rgb = image.convert("RGB")
            raw = rgb.tobytes()
            count = rgb.width * rgb.height
            totals = [0, 0, 0]
            for i in range(0, len(raw), 3):
                totals[0] += raw[i]
                totals[1] += raw[i + 1]
                totals[2] += raw[i + 2]
            average_color = (totals[0] // count, totals[1] // count, totals[2] // count)

            return ImageSummary(
                width=image.width,
                height=image.height,
                format=image.format or "unknown",
                average_color=average_color,
            )

        return await asyncio.to_thread(_run)
