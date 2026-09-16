"""Tests for LanguageAgent with mocked Gemini localization."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.language_agent import LanguageAgent
from config.settings import get_settings
from schemas.job import FeatureFlags, SourceType, VideoJobConfig
from schemas.localization import (
    GeminiLocalizedBatch,
    GeminiLocalizedClip,
    LocalizationTarget,
)
from schemas.project import ProjectMetadata
from schemas.story import ClipScript, ScriptsReport, StoryStructure


def _fake_localize(script_blocks, *, locale_block: str, **_kwargs) -> GeminiLocalizedBatch:
    assert script_blocks
    assert "Target language" in locale_block or "Language:" in locale_block
    return GeminiLocalizedBatch(
        scripts=[
            GeminiLocalizedClip(
                clip_id=0,
                title="स्थानीय शीर्षक",
                hook="ध्यान दें",
                short_script="स्थानीय स्क्रिप्ट सामग्री।",
                caption="कैप्शन",
                cta="फॉलो करें",
                thumbnail_text="टिप",
                keywords=["टिप", "हिंदी"],
                voice_direction="Warm Hindi delivery",
            )
        ]
    )


def test_language_agent_writes_localizations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "lang1"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="lang1", source_type=SourceType.SCRIPT, raw_text="x"
    )
    scripts = ScriptsReport(
        project_id="lang1",
        scripts=[
            ClipScript(
                clip_id=0,
                title="Key Tip",
                hook="Pay attention",
                short_script="Here is the tip.",
                caption="A tip",
                cta="Follow",
                thumbnail_text="Tip",
                keywords=["tip"],
                story_structure=StoryStructure(hook="Pay attention"),
            )
        ],
    )
    result = LanguageAgent(localize_fn=_fake_localize).run(
        project,
        project_dir=project_dir,
        scripts=scripts,
        config=VideoJobConfig(country="India", language="Hindi"),
    )
    path = Path(result.localizations_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["versions"]) == 1
    script = data["versions"][0]["scripts"][0]
    assert script["title"]
    assert script["hook"]
    assert script["short_script"]
    assert script["caption"]
    assert script["cta"]
    assert script["thumbnail_text"]
    assert script["keywords"]
    assert script["voice_direction"]
    assert script["locale"]["language"] == "Hindi"
    get_settings.cache_clear()


def test_language_agent_multi_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "lang2"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="lang2", source_type=SourceType.SCRIPT, raw_text="x"
    )
    scripts = ScriptsReport(
        project_id="lang2",
        scripts=[
            ClipScript(
                clip_id=0,
                title="Tip",
                hook="Hook",
                short_script="Body",
                caption="Cap",
                cta="CTA",
                thumbnail_text="Tip",
                keywords=["a"],
            )
        ],
    )
    calls: list[str] = []

    def _localize(script_blocks, *, locale_block: str, **_kwargs):
        calls.append(locale_block)
        return GeminiLocalizedBatch(
            scripts=[
                GeminiLocalizedClip(
                    clip_id=0,
                    title="T",
                    hook="H",
                    short_script="S",
                    caption="C",
                    cta="A",
                    thumbnail_text="Th",
                    keywords=["k"],
                    voice_direction="V",
                )
            ]
        )

    result = LanguageAgent(localize_fn=_localize).run(
        project,
        project_dir=project_dir,
        scripts=scripts,
        config=VideoJobConfig(
            country="India",
            region="Gujarat",
            language="English",
            localization_targets=[
                LocalizationTarget(
                    country="India", region="Gujarat", language="Gujarati"
                )
            ],
        ),
        features=FeatureFlags(cultural_adaptation=True),
    )
    assert len(result.localizations.versions) >= 2
    assert len(calls) == len(result.localizations.versions)
    get_settings.cache_clear()


def test_language_agent_empty_scripts_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "lang3"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="lang3", source_type=SourceType.SCRIPT, raw_text="x"
    )

    def _should_not_run(*_a, **_k):
        raise AssertionError("Gemini should not run")

    result = LanguageAgent(localize_fn=_should_not_run).run(
        project,
        project_dir=project_dir,
        scripts=ScriptsReport(project_id="lang3", scripts=[]),
        config=VideoJobConfig(country="USA", language="English"),
    )
    assert result.localizations.versions == []
    assert result.localizations.provider == "skipped"
    get_settings.cache_clear()
