from fastapi.testclient import TestClient

from jarvis.agents.base import AgentReply
from jarvis.api.app import create_app
from jarvis.voice.pipeline import VoiceTurnResult


class _FakeAgent:
    async def respond(self, session_id: str, user_message: str) -> AgentReply:
        return AgentReply(content=f"echo: {user_message}")


class _FakeVoicePipeline:
    """Satisfies the shape `create_app` needs from `VoicePipeline`, with no
    real STT/TTS models loaded.
    """

    def __init__(self) -> None:
        self.received: list[tuple[str, bytes]] = []

    async def handle_turn(self, session_id: str, audio_in: bytes) -> VoiceTurnResult:
        self.received.append((session_id, audio_in))
        return VoiceTurnResult(
            transcript="fake transcript", reply_text="fake reply", audio=b"fake-reply-audio"
        )


def test_voice_websocket_round_trip() -> None:
    fake_pipeline = _FakeVoicePipeline()
    app = create_app(coordinator=_FakeAgent(), voice_pipeline=fake_pipeline)  # type: ignore[arg-type]
    client = TestClient(app)

    with client.websocket_connect("/ws/voice") as websocket:
        websocket.send_bytes(b"fake-audio-in")
        reply_audio = websocket.receive_bytes()

    assert reply_audio == b"fake-reply-audio"
    assert fake_pipeline.received[0][1] == b"fake-audio-in"


def test_voice_websocket_maintains_one_session_per_connection() -> None:
    fake_pipeline = _FakeVoicePipeline()
    app = create_app(coordinator=_FakeAgent(), voice_pipeline=fake_pipeline)  # type: ignore[arg-type]
    client = TestClient(app)

    with client.websocket_connect("/ws/voice") as websocket:
        websocket.send_bytes(b"first")
        websocket.receive_bytes()
        websocket.send_bytes(b"second")
        websocket.receive_bytes()

    session_ids = {session_id for session_id, _ in fake_pipeline.received}
    assert len(session_ids) == 1


def test_voice_websocket_closes_cleanly_when_not_configured() -> None:
    # No voice_pipeline override and no JARVIS_PIPER_VOICE_MODEL_PATH set:
    # the endpoint must close with a clear reason, not crash the app.
    app = create_app(coordinator=_FakeAgent())  # type: ignore[arg-type]
    client = TestClient(app)

    with client.websocket_connect("/ws/voice") as websocket:
        close_message = websocket.receive()

    assert close_message["type"] == "websocket.close"
    assert close_message["code"] == 1011
    assert close_message["reason"] == "voice not configured"
