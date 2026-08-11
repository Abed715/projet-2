import asyncio
from typing import cast

import pytest
import websockets

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_chat_round_trip_through_real_server_redis_and_llm_http_call(
    backend_base_url: str, fake_anthropic_server: tuple[str, list[dict[str, object]]]
) -> None:
    """Drives a real WebSocket connection against the real `uvicorn`
    process from `backend_base_url`, which in turn makes a real HTTP call
    to the fake Anthropic server - proving the whole request path (ASGI
    server, WS handshake, `ConversationEngine`, real Redis-backed
    `ShortTermMemory`, the Anthropic SDK's real HTTP client) works,
    without a real Anthropic API key or a real call to Anthropic.
    """
    _anthropic_base_url, received_requests = fake_anthropic_server
    ws_url = backend_base_url.replace("http://", "ws://", 1) + "/ws/chat"

    async with websockets.connect(ws_url, proxy=None) as websocket:
        await websocket.send("hello from e2e test")
        first_reply = await asyncio.wait_for(websocket.recv(), timeout=10)

        await websocket.send("second turn")
        second_reply = await asyncio.wait_for(websocket.recv(), timeout=10)

    assert first_reply == "echo: hello from e2e test"
    assert second_reply == "echo: second turn"

    # Proves session history actually round-tripped through real Redis:
    # the second call to the LLM should see both turns, not just the
    # latest one.
    assert len(received_requests) == 2
    first_messages = cast("list[dict[str, object]]", received_requests[0]["messages"])
    second_messages = cast("list[dict[str, object]]", received_requests[1]["messages"])
    assert [m["content"] for m in first_messages] == ["hello from e2e test"]
    assert [m["content"] for m in second_messages] == [
        "hello from e2e test",
        "echo: hello from e2e test",
        "second turn",
    ]
