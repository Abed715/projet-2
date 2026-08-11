import asyncio

import pytest
import websockets
from websockets.exceptions import ConnectionClosed

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_voice_websocket_closes_cleanly_against_a_real_server(
    backend_base_url: str,
) -> None:
    """`backend_base_url` never sets JARVIS_PIPER_VOICE_MODEL_PATH, so the
    real server should accept the connection and then close it with the
    documented "not configured" reason - proving that failure path works
    over a real socket, not just through `TestClient`.
    """
    ws_url = backend_base_url.replace("http://", "ws://", 1) + "/ws/voice"

    async with websockets.connect(ws_url, proxy=None) as websocket:
        with pytest.raises(ConnectionClosed):
            await asyncio.wait_for(websocket.recv(), timeout=10)
        close_code = websocket.close_code
        close_reason = websocket.close_reason

    assert close_code == 1011
    assert close_reason == "voice not configured"
