import pytest

from jarvis.agents.base import AgentReply
from jarvis.voice.pipeline import VoicePipeline


class _FakeSTTProvider:
    async def transcribe(self, audio: bytes) -> str:
        return f"transcribed:{audio.decode()}"


class _FakeTTSProvider:
    async def synthesize(self, text: str) -> bytes:
        return f"audio:{text}".encode()


class _FakeCoordinator:
    def __init__(self) -> None:
        self.received: tuple[str, str] | None = None

    async def respond(self, session_id: str, user_message: str) -> AgentReply:
        self.received = (session_id, user_message)
        return AgentReply(content=f"reply-to:{user_message}")


@pytest.mark.asyncio
async def test_handle_turn_runs_stt_coordinator_tts_in_order() -> None:
    coordinator = _FakeCoordinator()
    pipeline = VoicePipeline(
        stt=_FakeSTTProvider(), tts=_FakeTTSProvider(), coordinator=coordinator
    )

    result = await pipeline.handle_turn("s1", b"hello")

    assert result.transcript == "transcribed:hello"
    assert coordinator.received == ("s1", "transcribed:hello")
    assert result.reply_text == "reply-to:transcribed:hello"
    assert result.audio == b"audio:reply-to:transcribed:hello"
