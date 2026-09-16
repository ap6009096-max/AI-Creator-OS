"""Tests for creator stage map and plan-phase checkpoint helpers."""

from __future__ import annotations

import json
from pathlib import Path

from ui.stage_map import (
    NODE_TO_STAGE,
    STAGES,
    agent_card_from_state,
    stage_for_node,
    stage_statuses_from_state,
)


def test_stage_count_is_seven() -> None:
    assert len(STAGES) == 7
    assert [s.id for s in STAGES] == [
        "understand",
        "research",
        "plan",
        "create",
        "produce",
        "review",
        "export",
    ]


def test_node_to_stage_mapping() -> None:
    assert stage_for_node("supervisor") == "understand"
    assert stage_for_node("research") == "research"
    assert stage_for_node("story") == "plan"
    assert stage_for_node("script") == "create"
    assert stage_for_node("storyboard") == "create"
    assert stage_for_node("render") == "produce"
    assert stage_for_node("quality") == "review"
    assert stage_for_node("export") == "export"
    assert "smart_clip" in NODE_TO_STAGE


def test_stage_statuses_from_artifacts() -> None:
    state = {
        "status": "running",
        "project": {"project_id": "p1"},
        "research": {"skipped": True},
        "stories": {"stories": []},
        "scripts": {"scripts": [{"clip_id": 0}]},
        "storyboard": {"frames": [{"frame_index": 0}]},
        "messages": ["[storyboard] Wrote analysis/storyboard.json"],
    }
    statuses = stage_statuses_from_state(state)
    assert statuses["understand"] == "completed"
    assert statuses["research"] == "completed"
    assert statuses["create"] == "completed"
    card = agent_card_from_state(state)
    assert "progress" in card
    assert card["model"] == "Gemini"


def test_checkpoint_roundtrip(tmp_path: Path) -> None:
    state = {
        "status": "completed",
        "project_dir": str(tmp_path),
        "stories": {"stories": [{"structure": {"hook": "Hi"}}]},
        "stop_after_storyboard": True,
    }
    path = tmp_path / "checkpoint_plan.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["stories"]["stories"][0]["structure"]["hook"] == "Hi"
    assert loaded["stop_after_storyboard"] is True
