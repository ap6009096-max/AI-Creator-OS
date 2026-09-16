"""Tests for CountryAgent and RegionalAgent (no Gemini)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.country_agent import CountryAgent
from agents.regional_agent import RegionalAgent
from config.settings import get_settings
from schemas.job import FeatureFlags, SourceType, VideoJobConfig
from schemas.project import ProjectMetadata


def test_country_agent_writes_locale_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "loc1"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="loc1", source_type=SourceType.SCRIPT, raw_text="x"
    )
    result = CountryAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(country="India", language="Hindi"),
    )
    assert result.country_profile is not None
    assert result.country_profile.name == "India"
    assert result.country_profile.default_language == "Hindi"
    path = Path(result.locale_context_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["country_profile"]["currency"]["code"] == "INR"
    get_settings.cache_clear()


def test_regional_agent_gujarat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "loc2"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="loc2", source_type=SourceType.SCRIPT, raw_text="x"
    )
    country = CountryAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(country="India", region="Gujarat", language="Gujarati"),
    )
    result = RegionalAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(country="India", region="Gujarat", language="Gujarati"),
        features=FeatureFlags(regional_humor=True),
        country_profile=country.country_profile,
    )
    assert result.region_profile is not None
    assert result.region_profile.name == "Gujarat"
    assert result.region_profile.language == "Gujarati"
    assert result.locale_pack is not None
    assert result.locale_pack.include_regional_humor is True
    data = json.loads(Path(result.locale_context_path).read_text(encoding="utf-8"))
    assert data["region_profile"]["name"] == "Gujarat"
    get_settings.cache_clear()


def test_regional_agent_continental_passthrough(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "loc3"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="loc3", source_type=SourceType.SCRIPT, raw_text="x"
    )
    result = RegionalAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(country="Japan", region="Asia", language="Japanese"),
    )
    assert result.region_profile is None
    assert result.locale_pack is not None
    assert result.locale_pack.country is not None
    assert result.locale_pack.country.name == "Japan"
    get_settings.cache_clear()
