"""TTS provider abstraction — passthrough when no real provider is configured."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from schemas.av_plan import VoicePlan


class TTSProvider(Protocol):
    name: str

    def is_available(self) -> bool: ...

    def synthesize(
        self,
        text: str,
        *,
        voice_plan: VoicePlan,
        out_path: Path,
    ) -> Path | None: ...


class PassthroughTTSProvider:
    """No-op provider: never writes audio; callers must preserve original."""

    name = "passthrough"

    def is_available(self) -> bool:
        return True

    def synthesize(
        self,
        text: str,
        *,
        voice_plan: VoicePlan,
        out_path: Path,
    ) -> Path | None:
        _ = (text, voice_plan, out_path)
        return None


def get_tts_provider() -> TTSProvider:
    """Return configured TTS provider, or passthrough when unset/unknown."""
    from config.settings import get_settings

    settings = get_settings()
    raw = (settings.tts_provider or "").strip().lower()
    if not raw or raw in {"passthrough", "none", "null"}:
        return PassthroughTTSProvider()
    # Future providers (e.g. elevenlabs) would branch here.
    # Unknown names fall back to passthrough so jobs never invent audio.
    return PassthroughTTSProvider()
