"""Tests for ScriptAgent with mocked Gemini generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.script_agent import ScriptAgent
from config.settings import get_settings
from schemas.clips import ClipCandidate, ClipsReport
from schemas.job import SourceType, VideoJobConfig
from schemas.project import ProjectMetadata
from schemas.story import (
    ClipStory,
    GeminiClipScript,
    GeminiScriptsBatch,
    StoriesReport,
    StoryStructure,
)


def _fake_scripts(clip_blocks, **_kwargs) -> GeminiScriptsBatch:
    assert clip_blocks
    return GeminiScriptsBatch(
        scripts=[
            GeminiClipScript(
                clip_id=0,
                title="Key Insight Clip",
                hook="Attention: the key insight starts here",
                short_script=(
                    "Attention: the key insight starts here. "
                    "Viewers need a brief setup. "
                    "The core tip from the source. "
                    "Why it matters. Follow for more tips."
                ),
                caption="A practical tip worth sharing.",
                cta="Follow for more tips",
                thumbnail_text="Key Insight",
                keywords=["insight", "tips", "shortform"],
            )
        ]
    )


def test_script_agent_writes_scripts_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "sc1"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="sc1", source_type=SourceType.SCRIPT, raw_text="x"
    )
    clips = ClipsReport(
        project_id="sc1",
        clips=[
            ClipCandidate(
                id=0,
                start=0.0,
                end=20.0,
                duration=20.0,
                transcript="The key insight starts here with a practical tip.",
                category="important",
                score=0.9,
            )
        ],
    )
    stories = StoriesReport(
        project_id="sc1",
        stories=[
            ClipStory(
                clip_id=0,
                start=0.0,
                end=20.0,
                structure=StoryStructure(
                    hook="Attention: the key insight starts here",
                    context="Viewers need a brief setup",
                    value_event="The core tip from the source",
                    payoff="Why it matters in practice",
                    cta="Follow for more tips",
                ),
                source_excerpt="The key insight starts here with a practical tip.",
            )
        ],
    )

    result = ScriptAgent(generate_fn=_fake_scripts).run(
        project,
        project_dir=project_dir,
        clips=clips,
        stories=stories,
        config=VideoJobConfig(video_type="Short-form"),
    )
    path = Path(result.scripts_path)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    script = data["scripts"][0]
    assert script["title"]
    assert script["hook"]
    assert script["short_script"]
    assert script["caption"]
    assert script["cta"]
    assert script["thumbnail_text"]
    assert script["keywords"]
    assert script["story_structure"]["hook"]
    get_settings.cache_clear()


def test_script_agent_empty_stories_skips_gemini(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "sc2"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="sc2", source_type=SourceType.SCRIPT, raw_text="x"
    )

    def _should_not_run(*_a, **_k):
        raise AssertionError("Gemini should not be called without stories")

    result = ScriptAgent(generate_fn=_should_not_run).run(
        project,
        project_dir=project_dir,
        clips=ClipsReport(project_id="sc2", clips=[]),
        stories=StoriesReport(project_id="sc2", stories=[]),
    )
    assert result.scripts.scripts == []
    assert result.scripts.provider == "skipped"
    assert Path(result.scripts_path).is_file()
    get_settings.cache_clear()
