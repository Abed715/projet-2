# jarvis.voice

**Status:** implemented (Phase 5). Depends on `jarvis.core` and
`jarvis.agents` (`VoicePipeline` drives an `Agent`, currently the
Coordinator).

## Public interface

```python
from jarvis.voice import (
    STTProvider, TTSProvider,
    FasterWhisperSTTProvider, PiperTTSProvider,
    WakeWordDetector, OpenWakeWordDetector,
    VoicePipeline, VoiceTurnResult, ConversationalAgent,
)
```

- **`STTProvider`** / **`TTSProvider`** — `Protocol` interfaces (mirrors
  `brain.providers.base.LLMProvider`): `transcribe(audio: bytes) -> str`
  and `synthesize(text: str) -> bytes` (WAV). One interface, swappable
  backends, per ARCHITECTURE.md §4's provider-abstraction note.
- **`FasterWhisperSTTProvider(model)`** — real adapter over
  `faster_whisper.WhisperModel`. `model` is typed `Any`, not the concrete
  SDK class, so tests inject a lightweight double instead of loading real
  Whisper weights.
- **`PiperTTSProvider(voice)`** — real adapter over `piper.PiperVoice`.
  Same `Any`-typed constructor for the same reason: tests never load a
  real Piper voice model (an `.onnx` file the deployment supplies).
- **`WakeWordDetector`** — `Protocol`: `detect(audio_frame: bytes) -> bool`.
  **`OpenWakeWordDetector(model, *, wake_word, threshold=0.5)`** — real
  adapter over `openwakeword.model.Model`, same `Any`-typed pattern.
- **`VoicePipeline(*, stt, tts, coordinator)`** — `handle_turn(session_id,
  audio_in) -> VoiceTurnResult(transcript, reply_text, audio)`: transcribe
  → feed the transcript through a `ConversationalAgent` (currently the
  Coordinator, an `agents.Agent`) → synthesize the reply. This is what
  `/ws/voice` in `jarvis.api` calls per turn.
- **`ConversationalAgent`** — `Protocol` capturing just the `respond(...)`
  shape `VoicePipeline` needs, deliberately narrower than the concrete
  `agents.Agent` class so tests inject a fake coordinator instead of
  wiring a real `ConversationEngine`.

## Design notes

- **Why providers take an already-constructed model instead of loading one
  themselves:** `ClaudeProvider` takes an already-constructed
  `anthropic.AsyncAnthropic` client for the same reason — constructing the
  client is production wiring (`api/app.py`'s `_build_default_*` helpers),
  not something the provider class should do, and it keeps the provider
  trivially testable with a double. It matters more here than for Claude:
  loading a real `WhisperModel` or `PiperVoice` means downloading or
  supplying multi-hundred-MB model weights, which the test suite must
  never do (same "no real network/model calls in tests" rule as every
  other module).
- **Non-streaming, turn-based `/ws/voice`, like `/ws/chat` was in Phase
  2:** one binary WS message in (a full utterance's audio), one binary
  message out (the synthesized reply). Streaming partial transcripts,
  voice activity detection (VAD) to detect end-of-utterance automatically,
  and barge-in/interrupt (stopping TTS playback when the user starts
  talking again) are all real product features from ARCHITECTURE.md's
  Phase 5 scope, deferred here the same way Phase 2's `/ws/chat` deferred
  token-by-token streaming: this is the simplest thing that proves the
  stack end to end, and each of those is a genuine feature addition, not
  a bug fix, once there's a client to drive them.
- **Wake word is implemented but not wired into `/ws/voice`:**
  `OpenWakeWordDetector` is a complete, tested component, but continuous
  wake-word listening needs a persistent audio-frame stream and
  activation state machine that doesn't fit `/ws/voice`'s one-shot,
  client-triggered turn model. Wiring it in is a Phase 7 (desktop)
  concern — a global hotkey or an always-listening capture loop belongs
  in the Electron shell / a client, not the request/reply backend
  endpoint.
- Every model class here is headless-safe to *import* (verified directly:
  `faster_whisper`, `piper`, `openwakeword` all import without touching
  audio hardware or a display — unlike `pyautogui` in Phase 4). The
  hardware constraint Phase 4 designed around (crashes at import/
  construction time without a display) simply doesn't apply to speech
  libraries operating on in-memory audio bytes; the real constraint here
  is model-weight availability, handled by dependency injection instead.

## Known limitations / deferred

- No streaming STT/TTS, VAD, or barge-in/interrupt (see above).
- No emotion tagging (ARCHITECTURE.md's `voice/` description mentions it;
  no concrete use case yet).
- `OpenWakeWordDetector` is untested against real audio (no bundled
  wake-word model weights are downloaded in CI); it's exercised in tests
  with a fake `model.predict(...)` double, same as `FasterWhisperSTTProvider`
  and `PiperTTSProvider`.
- No ElevenLabs (cloud TTS) adapter yet — ARCHITECTURE.md lists it as an
  optional, flagged alternative to Piper; add it if/when higher voice
  quality is actually needed, following the same `TTSProvider` interface.
