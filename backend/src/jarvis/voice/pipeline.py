"""Voice turn pipeline: audio in -> transcript -> Coordinator reply ->
audio out. This is the non-streaming "prove the stack end to end" cut,
matching how `/ws/chat` started in Phase 2 — one WS message in, one
message out. Streaming partial transcripts, VAD, and barge-in/interrupt
are deferred; see `voice/README.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from jarvis.agents.base import AgentReply
from jarvis.voice.providers.base import STTProvider, TTSProvider


class ConversationalAgent(Protocol):
    """The slice of `agents.Agent` `VoicePipeline` needs — narrow on
    purpose so tests can inject a fake coordinator double instead of a
    real `Agent` wired to `ConversationEngine`.
    """

    async def respond(self, session_id: str, user_message: str) -> AgentReply: ...


@dataclass(frozen=True, slots=True)
class VoiceTurnResult:
    transcript: str
    reply_text: str
    audio: bytes


class VoicePipeline:
    def __init__(
        self, *, stt: STTProvider, tts: TTSProvider, coordinator: ConversationalAgent
    ) -> None:
        self._stt = stt
        self._tts = tts
        self._coordinator = coordinator

    async def handle_turn(self, session_id: str, audio_in: bytes) -> VoiceTurnResult:
        transcript = await self._stt.transcribe(audio_in)
        reply = await self._coordinator.respond(session_id, transcript)
        audio_out = await self._tts.synthesize(reply.content)
        return VoiceTurnResult(transcript=transcript, reply_text=reply.content, audio=audio_out)
