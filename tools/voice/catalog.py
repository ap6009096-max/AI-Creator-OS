"""Load and resolve voice presets from config/voices.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from schemas.av_plan import VoicePack, VoicePlan, VoicePreset
from tools.voice.provider import get_tts_provider

_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "voices.json"


def _norm(value: str) -> str:
    return " ".join(
        (value or "").strip().lower().replace("_", " ").replace("-", " ").split()
    )


@lru_cache(maxsize=1)
def _load_raw() -> list[dict[str, Any]]:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def clear_voice_cache() -> None:
    _load_raw.cache_clear()


def list_voices() -> list[VoicePreset]:
    return [VoicePreset.model_validate(item) for item in _load_raw()]


def resolve_voice(name_or_id: str) -> VoicePreset | None:
    key = _norm(name_or_id)
    if not key:
        return None
    for preset in list_voices():
        if _norm(preset.id) == key or _norm(preset.name) == key:
            return preset
        for alias in preset.aliases:
            if _norm(alias) == key:
                return preset
    return None


def _fallback_preset(label: str) -> VoicePreset:
    return VoicePreset(
        id="fallback_original",
        name=label.strip() or "Original Voice",
        mode="original",
        notes="Unknown voice label — falling back to original audio.",
    )


def build_voice_pack(
    voice_label: str,
    *,
    language: str = "",
    enabled: bool = True,
) -> VoicePack:
    label = (voice_label or "").strip() or "Original Voice"
    preset = resolve_voice(label)
    fallback = False
    if preset is None:
        preset = _fallback_preset(label)
        fallback = True

    provider = get_tts_provider()
    provider_ready = bool(provider.is_available() and provider.name != "passthrough")
    # Passthrough is always "available" as a no-op but not a real TTS engine.
    real_tts = provider.name != "passthrough" and provider.is_available()

    preserve = True
    notes_parts: list[str] = []
    if not enabled:
        notes_parts.append("Voice feature flag off — preserving original audio.")
        preserve = True
    elif preset.mode == "original" or fallback:
        notes_parts.append("Original voice mode — preserving source audio.")
        preserve = True
    elif preset.mode == "ai_tts" and not real_tts:
        notes_parts.append(
            "AI Voice requested but no TTS provider configured — preserving original audio."
        )
        preserve = True
    elif preset.mode in ("ai_tts", "talent_direction") and not real_tts:
        notes_parts.append(
            f"Voice direction '{preset.name}' recorded; "
            "no TTS provider — preserving original audio for MVP."
        )
        preserve = True
    elif real_tts and preset.mode == "ai_tts":
        preserve = False
        notes_parts.append(f"TTS provider '{provider.name}' ready for synthesis.")
    else:
        notes_parts.append(
            f"Talent direction '{preset.name}' planned; synthesis not required for MVP."
        )
        preserve = True

    lang = (preset.language_hint or language or "").strip()
    direction = (
        f"{preset.gender or 'neutral'} voice"
        + (f", language={lang}" if lang else "")
        + (f". {preset.notes}" if preset.notes else "")
    ).strip()

    plan = VoicePlan(
        preset_name=preset.name,
        mode=preset.mode,
        preserve_original=preserve,
        provider=provider.name,
        provider_ready=real_tts,
        gender=preset.gender,
        language_hint=lang,
        direction=direction,
        audio_path="",
        notes=" ".join(notes_parts),
    )
    return VoicePack(
        source_label=label,
        preset=preset,
        plan=plan,
        fallback=fallback,
        notes=plan.notes,
    )
