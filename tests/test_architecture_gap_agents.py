"""Unit tests for Supervisor, Research, Storyboard, Analytics agents and research routing."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.analytics_agent import AnalyticsAgent
from agents.research_agent import ResearchAgent
from agents.storyboard_agent import StoryboardAgent
from agents.supervisor_agent import SupervisorAgent
from config.settings import get_settings
from graph.routers import (
    route_after_smart_clip_research,
    should_run_research,
)
from schemas.job import FeatureFlags, SourceType, VideoJobConfig, VideoJobRequest
from schemas.project import ProjectMetadata
from schemas.research import GeminiResearchPlan
from schemas.storyboard import GeminiStoryboardBatch, GeminiStoryboardFrame
from tools.research.parallel_search import ParallelSearchResult


def test_should_run_research_flag() -> None:
    assert should_run_research({"job": {"features": {"enable_research": True}}}) is True
    assert should_run_research({"job": {"features": {"enable_research": False}}}) is False
    # Default FeatureFlags enable_research=True
    assert should_run_research({"job": {"features": {}}}) is True


def test_route_after_smart_clip_research() -> None:
    on = {"job": {"features": {"enable_research": True}}, "status": "running"}
    assert route_after_smart_clip_research(on) == "research"
    off = {"job": {"features": {"enable_research": False}}, "status": "running"}
    assert route_after_smart_clip_research(off) == "skip_research"
    failed = {
        "job": {"features": {"enable_research": True}},
        "status": "failed",
        "error": "x",
    }
    assert route_after_smart_clip_research(failed) == "smart_clip_failed"


def test_supervisor_agent_plan() -> None:
    req = VideoJobRequest(
        source_type=SourceType.SCRIPT,
        script_text="Hello world content idea for shorts",
        config=VideoJobConfig(platform="YouTube Shorts"),
        features=FeatureFlags(enable_research=True),
    )
    result = SupervisorAgent().run(req)
    state = result.to_state_dict()
    assert state["next_agent"] == "input"
    assert state["supervisor"]["source_type"] == "script"
    assert "research" in state["supervisor"]["planned_stages"]
    assert state["supervisor"]["feature_summary"]["enable_research"] is True


def test_research_agent_soft_skip_without_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("PARALLEL_API_KEY", "")
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "r1"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="r1", source_type=SourceType.SCRIPT, raw_text="AI video tips"
    )
    result = ResearchAgent().run(
        project,
        project_dir=project_dir,
        features=FeatureFlags(enable_research=True),
    )
    assert result.research.skipped is True
    assert Path(result.research_path).is_file()
    get_settings.cache_clear()


def test_research_agent_with_mocked_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("PARALLEL_API_KEY", "test-key")
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "r2"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="r2", source_type=SourceType.SCRIPT, raw_text="AI video tips"
    )

    def fake_plan(**_kwargs: object) -> GeminiResearchPlan:
        return GeminiResearchPlan(
            objective="Find AI video trends",
            search_queries=["AI video trends", "shorts tips", "creator tools"],
        )

    def fake_search(**_kwargs: object) -> ParallelSearchResult:
        return ParallelSearchResult(
            objective="Find AI video trends",
            search_queries=["AI video trends", "shorts tips", "creator tools"],
            results=[
                {
                    "title": "Trend report",
                    "url": "https://example.com",
                    "excerpts": ["Shorts are rising"],
                }
            ],
        )

    result = ResearchAgent(plan_fn=fake_plan, search_fn=fake_search).run(
        project,
        project_dir=project_dir,
        features=FeatureFlags(enable_research=True),
        clips={"clips": [{"id": 0, "title": "Tip", "transcript": "Use hooks"}]},
    )
    assert result.research.skipped is False
    assert len(result.research.results) == 1
    data = json.loads(Path(result.research_path).read_text(encoding="utf-8"))
    assert data["results"][0]["title"] == "Trend report"
    get_settings.cache_clear()


def test_storyboard_agent_writes_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "sb1"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="sb1", source_type=SourceType.SCRIPT, raw_text="x"
    )

    def fake_board(**_kwargs: object) -> GeminiStoryboardBatch:
        return GeminiStoryboardBatch(
            frames=[
                GeminiStoryboardFrame(
                    frame_index=0,
                    clip_id=0,
                    shot_intent="Hook close-up",
                    on_screen_text="Stop scrolling",
                    narration="Here is the tip",
                    duration_hint_sec=3.5,
                    visual_notes="High contrast",
                )
            ]
        )

    result = StoryboardAgent(generate_fn=fake_board).run(
        project,
        project_dir=project_dir,
        scripts={
            "scripts": [
                {
                    "clip_id": 0,
                    "title": "Tip",
                    "hook": "Stop scrolling",
                    "short_script": "Here is the tip",
                    "cta": "Follow",
                }
            ]
        },
    )
    assert len(result.storyboard.frames) == 1
    assert Path(result.storyboard_path).is_file()
    get_settings.cache_clear()


def test_analytics_agent_rollup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    project_dir = tmp_path / "outputs" / "projects" / "a1"
    project_dir.mkdir(parents=True)
    project = ProjectMetadata(
        project_id="a1", source_type=SourceType.SCRIPT, raw_text="x"
    )
    result = AnalyticsAgent().run(
        project,
        project_dir=project_dir,
        config=VideoJobConfig(platform="YouTube Shorts", language="English"),
        clips={"clips": [{"id": 0, "duration": 12.0}, {"id": 1, "duration": 8.0}]},
        stories={"stories": [{"clip_id": 0}]},
        scripts={"scripts": [{"clip_id": 0}, {"clip_id": 1}]},
        storyboard={"frames": [{"frame_index": 0}, {"frame_index": 1}]},
        research={"results": [{"title": "t"}]},
        quality_pack={"report": {"passed": True, "skipped": False}},
        render_pack={"plan": {"skipped": False, "encoded": True}},
    )
    report = result.analytics.report
    assert report.clip_count == 2
    assert report.script_count == 2
    assert report.storyboard_frame_count == 2
    assert report.research_result_count == 1
    assert report.quality_passed is True
    assert report.estimated_duration_sec == 20.0
    assert Path(result.analytics_path).is_file()
    state = result.to_state_dict()
    assert "analytics" in state
    get_settings.cache_clear()


def test_parallel_search_normalizes_results(monkeypatch: pytest.MonkeyPatch) -> None:
    from tools.research.parallel_search import run_parallel_search

    class FakeClient:
        def search(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                results=[
                    SimpleNamespace(
                        title="A",
                        url="https://a.example",
                        excerpts=["one", "two"],
                    )
                ]
            )

    monkeypatch.setenv("PARALLEL_API_KEY", "k")
    get_settings.cache_clear()
    out = run_parallel_search(
        objective="obj",
        search_queries=["q1", "q2", "q3"],
        client=FakeClient(),
    )
    assert out.results[0]["title"] == "A"
    assert out.results[0]["excerpts"] == ["one", "two"]
    get_settings.cache_clear()
