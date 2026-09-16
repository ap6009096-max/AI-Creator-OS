"""Unit tests for graph routers."""

from __future__ import annotations

from graph.routers import (
    should_run_broll,
    should_run_funny,
    should_run_music,
    should_run_research,
    should_run_viral,
    should_run_voice,
    route_after_moment,
    route_after_environment,
    route_after_smart_clip_research,
)


def test_funny_skip_when_flag_off() -> None:
    state = {"job": {"features": {"funny_moments": False, "smart_clip_detection": True}}}
    assert should_run_funny(state) is False
    assert route_after_moment({**state, "status": "running"}) == "skip_funny"


def test_viral_on_by_default() -> None:
    state = {"job": {"features": {}}}
    assert should_run_viral(state) is True


def test_voice_original_skips() -> None:
    state = {
        "job": {
            "features": {"voice": True},
            "config": {"voice": "Original Voice"},
        }
    }
    assert should_run_voice(state) is False


def test_music_no_music_skips() -> None:
    state = {
        "job": {
            "features": {"music": True},
            "config": {"music": "No Music"},
        }
    }
    assert should_run_music(state) is False


def test_broll_route() -> None:
    off = {"job": {"features": {"b_roll": False}}, "status": "running"}
    assert should_run_broll(off) is False
    assert route_after_environment(off) == "skip_broll"
    on = {"job": {"features": {"b_roll": True}}, "status": "running"}
    assert route_after_environment(on) == "b_roll"


def test_research_route() -> None:
    off = {"job": {"features": {"enable_research": False}}, "status": "running"}
    assert should_run_research(off) is False
    assert route_after_smart_clip_research(off) == "skip_research"
    on = {"job": {"features": {"enable_research": True}}, "status": "running"}
    assert route_after_smart_clip_research(on) == "research"
