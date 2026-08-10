"""FastAPI application factory — the composition root for the backend."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import cast

import anthropic
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from jarvis.agents import Agent, create_coordinator
from jarvis.brain.conversation import ConversationEngine
from jarvis.brain.providers.claude import ClaudeProvider
from jarvis.brain.router import LLMRouter
from jarvis.core import (
    JarvisError,
    NotFoundError,
    PermissionDeniedError,
    Settings,
    ValidationError,
    configure_logging,
    create_redis_client,
    get_logger,
    get_settings,
)
from jarvis.core.logging import reset_correlation_id, set_correlation_id
from jarvis.memory.short_term import RedisLike, ShortTermMemory

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


def _build_default_coordinator(settings: Settings) -> Agent:
    """Wire the real, Claude-backed Coordinator from process settings.

    Kept separate from `create_app` so tests can bypass it entirely (via
    `create_app(coordinator=...)`) and never construct a real
    `anthropic.AsyncAnthropic` client or touch a real Redis server.
    """
    redis_client = create_redis_client(settings.redis_url)
    # `redis.asyncio.Redis`'s real method signatures (extra kwargs, broader
    # key/value types) don't structurally match the narrow `RedisLike`
    # protocol `ShortTermMemory` is tested against — see memory/README.md.
    memory = ShortTermMemory(cast(RedisLike, redis_client))

    router = LLMRouter()
    claude_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    router.register(
        "anthropic", ClaudeProvider(claude_client, model=settings.anthropic_model)
    )

    engine = ConversationEngine(memory=memory, router=router)
    return create_coordinator(engine, provider_name="anthropic")


def create_app(*, coordinator: Agent | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    `coordinator` is a dependency-injection seam: omit it in production to
    get the real Claude-backed Coordinator built from process settings, or
    pass a fake `Agent` in tests to exercise `/ws/chat` with no network
    calls and no real Redis server.
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

    resolved_coordinator = coordinator if coordinator is not None else _build_default_coordinator(
        settings
    )

    @app.websocket("/ws/chat")
    async def chat_websocket(websocket: WebSocket) -> None:
        session_id = str(uuid.uuid4())
        await websocket.accept()
        try:
            while True:
                user_message = await websocket.receive_text()
                reply = await resolved_coordinator.respond(session_id, user_message)
                await websocket.send_text(reply.content)
        except WebSocketDisconnect:
            logger.info("chat websocket disconnected session_id=%s", session_id)

    return app
