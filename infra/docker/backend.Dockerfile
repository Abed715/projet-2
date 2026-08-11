# syntax=docker/dockerfile:1
#
# Multi-stage build: compile/install the package + its dependencies in
# `builder` (non-editable `pip install .`, so the source is baked into
# site-packages - not bind-mounted, this is an immutable production
# image), ship only the installed tree + runtime system deps in
# `runtime`. No dev extras (pytest/ruff/mypy/...) end up in the final
# image.

FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# build-essential: some of automation/vision/voice's dependencies
# (scipy/scikit-learn transitively, for openwakeword) may need to compile
# from source on architectures without a prebuilt wheel. Discarded with
# this whole stage - never present in the runtime image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# tesseract-ocr: jarvis.vision.OcrService's only runtime dependency beyond
# what pip installs - see vision/README.md. libgomp1: OpenMP runtime some
# onnxruntime/ctranslate2 builds link against (voice/vision inference).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 jarvis

COPY --from=builder /install /usr/local

RUN mkdir -p /app/workspace && chown -R jarvis:jarvis /app

USER jarvis

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "jarvis.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
