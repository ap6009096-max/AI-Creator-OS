"""Tests for VoiceAgent."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.voice_agent import VoiceAgent
from config.settings import get_settings
from schemas.job import FeatureFlags, SourceType, VideoJobConfig
from schemas.project import ProjectMetadata


def test_voice_agent_original_preserves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "vo1"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="vo1", source_type=SourceType.SCRIPT, raw_text="x"
    )
    result = VoiceAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(voice="Original Voice"),
        features=FeatureFlags(voice=True),
    )
    path = Path(result.voice_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["plan"]["preserve_original"] is True
    assert data["preset"]["name"] == "Original Voice"
    get_settings.cache_clear()


def test_voice_agent_ai_without_provider_preserves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("TTS_PROVIDER", "")
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "vo2"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="vo2", source_type=SourceType.SCRIPT, raw_text="x"
    )
    result = VoiceAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(voice="AI Voice", language="English"),
        features=FeatureFlags(voice=True),
    )
    assert result.voice_pack.plan.preserve_original is True
    assert result.voice_pack.plan.provider_ready is False
    assert result.voice_pack.plan.audio_path == ""
    get_settings.cache_clear()


def test_voice_agent_flag_off_preserves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "vo3"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="vo3", source_type=SourceType.SCRIPT, raw_text="x"
    )
    result = VoiceAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(voice="AI Voice"),
        features=FeatureFlags(voice=False),
    )
    assert result.voice_pack.plan.preserve_original is True
    get_settings.cache_clear()
