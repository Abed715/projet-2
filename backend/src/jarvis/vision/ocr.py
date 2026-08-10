"""Optical character recognition over `pytesseract` + Pillow. Unlike most of
`vision`, this needs no display — verified to work fully headlessly (given
the `tesseract-ocr` system package) — so `OcrService` calls it directly
rather than through a swappable backend Protocol.
"""

from __future__ import annotations

import asyncio
import io

import pytesseract
from PIL import Image

from jarvis.core.exceptions import ConfigurationError, ValidationError


class OcrService:
    async def extract_text(self, image_bytes: bytes) -> str:
        if not image_bytes:
            raise ValidationError("image_bytes must not be empty")

        def _run() -> str:
            try:
                image = Image.open(io.BytesIO(image_bytes))
                image.load()
            except Exception as exc:
                raise ValidationError("could not decode image data") from exc
            try:
                return str(pytesseract.image_to_string(image))
            except pytesseract.TesseractNotFoundError as exc:
                raise ConfigurationError("tesseract-ocr is not installed") from exc

        return await asyncio.to_thread(_run)
