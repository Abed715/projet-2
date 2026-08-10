"""jarvis.voice — speech I/O: STT/TTS provider adapters, wake-word
detection, and the non-streaming voice-turn pipeline.

See README.md for the full public interface and design notes.
"""

from jarvis.voice.pipeline import ConversationalAgent, VoicePipeline, VoiceTurnResult
from jarvis.voice.providers import (
    FasterWhisperSTTProvider,
    PiperTTSProvider,
    STTProvider,
    TTSProvider,
)
from jarvis.voice.wake_word import OpenWakeWordDetector, WakeWordDetector

__all__ = [
    "ConversationalAgent",
    "FasterWhisperSTTProvider",
    "OpenWakeWordDetector",
    "PiperTTSProvider",
    "STTProvider",
    "TTSProvider",
    "VoicePipeline",
    "VoiceTurnResult",
    "WakeWordDetector",
]
