"""Feature/source conditional routing helpers for the video graph."""

from __future__ import annotations

from typing import Any

from schemas.base import JobStatus
from schemas.job import FeatureFlags, SourceType, VideoJobConfig


def _job(state: dict[str, Any]) -> dict[str, Any]:
    return state.get("job") or {}


def _features(state: dict[str, Any]) -> FeatureFlags:
    raw = _job(state).get("features") or {}
    if isinstance(raw, FeatureFlags):
        return raw
    try:
        return FeatureFlags.model_validate(raw)
    except Exception:  # noqa: BLE001
        return FeatureFlags()


def _config(state: dict[str, Any]) -> VideoJobConfig:
    raw = _job(state).get("config") or {}
    if isinstance(raw, VideoJobConfig):
        return raw
    try:
        return VideoJobConfig.model_validate(raw)
    except Exception:  # noqa: BLE001
        return VideoJobConfig()


def _failed(state: dict[str, Any]) -> bool:
    return state.get("status") == JobStatus.FAILED.value or bool(state.get("error"))


def is_script_source(state: dict[str, Any]) -> bool:
    source = _job(state).get("source_type") or ""
    if isinstance(source, SourceType):
        return source == SourceType.SCRIPT
    return str(source).lower() == SourceType.SCRIPT.value


def is_video_source(state: dict[str, Any]) -> bool:
    return not is_script_source(state)


def route_failed_or(state: dict[str, Any], failed_key: str, otherwise: str) -> str:
    if _failed(state):
        return failed_key
    return otherwise


def should_run_funny(state: dict[str, Any]) -> bool:
    f = _features(state)
    return bool(f.funny_moments and f.smart_clip_detection)


def should_run_viral(state: dict[str, Any]) -> bool:
    f = _features(state)
    return bool(f.viral_moments and f.smart_clip_detection)


def should_run_broll(state: dict[str, Any]) -> bool:
    return bool(_features(state).b_roll)


def should_run_voice(state: dict[str, Any]) -> bool:
    f = _features(state)
    cfg = _config(state)
    voice = (cfg.voice or "").strip().lower()
    if voice in {"original voice", "original", "none"}:
        return False
    return bool(f.voice)


def should_run_music(state: dict[str, Any]) -> bool:
    f = _features(state)
    cfg = _config(state)
    music = (cfg.music or "").strip().lower()
    if music in {"no music", "none", "off"}:
        return False
    return bool(f.music)


def should_run_research(state: dict[str, Any]) -> bool:
    """Run research when enabled; soft-skip path handles missing API key."""
    return bool(_features(state).enable_research)


def should_run_cultural(state: dict[str, Any]) -> bool:
    return bool(_features(state).cultural_adaptation)


def should_run_humor(state: dict[str, Any]) -> bool:
    f = _features(state)
    cfg = _config(state)
    if (cfg.humor_adaptation or "none") == "none":
        return False
    return bool(f.regional_humor)


def route_after_speaker(state: dict[str, Any]) -> str:
    """Speaker → moment detection (PROMPT 25 order)."""
    return route_failed_or(state, "speaker_analysis_failed", "continue")


def route_after_moment(state: dict[str, Any]) -> str:
    if _failed(state):
        return "moment_detection_failed"
    if should_run_funny(state):
        return "funny"
    return "skip_funny"


def route_after_funny(state: dict[str, Any]) -> str:
    if _failed(state):
        return "funny_moment_failed"
    if should_run_viral(state):
        return "viral"
    return "skip_viral"


def route_after_viral(state: dict[str, Any]) -> str:
    return route_failed_or(state, "viral_moment_failed", "continue")


def route_after_language(state: dict[str, Any]) -> str:
    if _failed(state):
        return "language_failed"
    if should_run_cultural(state):
        return "cultural"
    return "skip_cultural"


def route_after_cultural(state: dict[str, Any]) -> str:
    if _failed(state):
        return "cultural_failed"
    if should_run_humor(state):
        return "humor"
    return "skip_humor"


def route_after_humor(state: dict[str, Any]) -> str:
    return route_failed_or(state, "humor_failed", "continue")


def route_after_environment(state: dict[str, Any]) -> str:
    if _failed(state):
        return "environment_failed"
    if should_run_broll(state):
        return "b_roll"
    return "skip_broll"


def route_after_broll(state: dict[str, Any]) -> str:
    if _failed(state):
        return "b_roll_failed"
    if should_run_voice(state):
        return "voice"
    return "skip_voice"


def route_after_voice(state: dict[str, Any]) -> str:
    if _failed(state):
        return "voice_failed"
    if should_run_music(state):
        return "music"
    return "skip_music"


def route_after_music(state: dict[str, Any]) -> str:
    return route_failed_or(state, "music_failed", "continue")


def route_after_smart_clip_research(state: dict[str, Any]) -> str:
    if _failed(state):
        return "smart_clip_failed"
    if should_run_research(state):
        return "research"
    return "skip_research"


def route_after_research(state: dict[str, Any]) -> str:
    return route_failed_or(state, "research_failed", "continue")
