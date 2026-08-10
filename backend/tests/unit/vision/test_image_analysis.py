import io

import pytest
from PIL import Image

from jarvis.core.exceptions import ValidationError
from jarvis.vision.image_analysis import ImageAnalysisService, ImageSummary


def _solid_color_png(color: tuple[int, int, int], size: tuple[int, int] = (40, 20)) -> bytes:
    image = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def service() -> ImageAnalysisService:
    return ImageAnalysisService()


@pytest.mark.asyncio
async def test_analyze_returns_dimensions_and_format(service: ImageAnalysisService) -> None:
    summary = await service.analyze(_solid_color_png((255, 0, 0), size=(40, 20)))

    assert isinstance(summary, ImageSummary)
    assert summary.width == 40
    assert summary.height == 20
    assert summary.format == "PNG"


@pytest.mark.asyncio
async def test_analyze_computes_average_color_of_solid_image(
    service: ImageAnalysisService,
) -> None:
    summary = await service.analyze(_solid_color_png((10, 20, 30)))

    assert summary.average_color == (10, 20, 30)


@pytest.mark.asyncio
async def test_analyze_rejects_empty_bytes(service: ImageAnalysisService) -> None:
    with pytest.raises(ValidationError):
        await service.analyze(b"")


@pytest.mark.asyncio
async def test_analyze_rejects_invalid_image_data(service: ImageAnalysisService) -> None:
    with pytest.raises(ValidationError):
        await service.analyze(b"not an image")
