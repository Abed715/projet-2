import io

import pytest
from PIL import Image, ImageDraw

from jarvis.core.exceptions import ValidationError
from jarvis.vision.ocr import OcrService


def _render_text_png(text: str) -> bytes:
    image = Image.new("RGB", (200, 60), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), text, fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def service() -> OcrService:
    return OcrService()


@pytest.mark.asyncio
async def test_extract_text_reads_rendered_text(service: OcrService) -> None:
    image_bytes = _render_text_png("HELLO")

    text = await service.extract_text(image_bytes)

    assert "HELLO" in text


@pytest.mark.asyncio
async def test_extract_text_rejects_empty_bytes(service: OcrService) -> None:
    with pytest.raises(ValidationError):
        await service.extract_text(b"")


@pytest.mark.asyncio
async def test_extract_text_rejects_invalid_image_data(service: OcrService) -> None:
    with pytest.raises(ValidationError):
        await service.extract_text(b"not an image")
