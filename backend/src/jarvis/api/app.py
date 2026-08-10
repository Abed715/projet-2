"""FastAPI application factory — the composition root for the backend."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from jarvis.core import (
    JarvisError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
    configure_logging,
    get_logger,
    get_settings,
)
from jarvis.core.logging import reset_correlation_id, set_correlation_id

logger = get_logger(__name__)

_ERROR_STATUS_CODES: dict[type[JarvisError], int] = {
    NotFoundError: 404,
    ValidationError: 422,
    PermissionDeniedError: 403,
}


def _status_code_for(error: JarvisError) -> int:
    for error_type, status_code in _ERROR_STATUS_CODES.items():
        if isinstance(error, error_type):
            return status_code
    return 500


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Kept intentionally small: settings + logging + CORS + error handling +
    a health check. Domain routers are mounted here as they ship in later
    phases (see backend/src/jarvis/api/README.md).
    """
    settings = get_settings()
    configure_logging(level=settings.log_level, json_format=settings.is_production)

    app = FastAPI(title="JARVIS API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        token = set_correlation_id(correlation_id)
        try:
            response = await call_next(request)
        finally:
            reset_correlation_id(token)
        response.headers["x-correlation-id"] = correlation_id
        return response

    @app.exception_handler(JarvisError)
    async def jarvis_error_handler(request: Request, exc: JarvisError) -> JSONResponse:
        status_code = _status_code_for(exc)
        if status_code >= 500:
            logger.exception("unhandled JarvisError", exc_info=exc)
        return JSONResponse(
            status_code=status_code,
            content={"error": type(exc).__name__, "message": exc.message, "details": exc.details},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
