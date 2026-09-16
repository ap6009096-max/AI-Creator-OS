"""Shared Streamlit session helpers for the Creator OS UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from schemas.base import JobStatus
from schemas.job import initial_progress_steps
from ui.stage_map import STAGES


NAV_PAGES: list[tuple[str, str]] = [
    ("dashboard", "Dashboard & KPIs"),
    ("create", "New Video Package"),
    ("memory", "Creator Memory"),
    ("intelligence", "Viral Intelligence"),
    ("repurpose", "Content Repurposing"),
    ("calendar", "Smart Calendar"),
    ("multilingual", "Multilingual Factory"),
    ("qa", "AI QA Gate"),
    ("pipeline", "Pipeline"),
    ("plan", "Production Plan"),
    ("storyboard", "Storyboards"),
    ("preview", "Preview / Export"),
    ("projects", "Projects"),
    ("agents", "Agent Workflow"),
    ("settings", "Settings"),
]


def init_creator_session() -> None:
    """Ensure Creator OS session keys exist."""
    defaults: dict[str, Any] = {
        "nav_page": "create",
        "pipeline_steps": initial_progress_steps(),
        "pipeline_status": JobStatus.PENDING.value,
        "pipeline_error": None,
        "pipeline_messages": [],
        "last_result": None,
        "workflow_state": None,
        "project_checkpoint": None,
        "phase": "idle",  # idle | plan_ready | producing | done | failed
        "activity_log": [],
        "stage_statuses": {s.id: "pending" for s in STAGES},
        "agent_card": {
            "name": "Supervisor Agent",
            "status": "Idle",
            "model": "Gemini",
            "task": "Waiting for a create request",
            "progress": 0,
            "stage": "understand",
        },
        "plan_edits": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_page(page: str) -> None:
    st.session_state.nav_page = page


def append_activity(text: str) -> None:
    from datetime import datetime, timezone

    log = list(st.session_state.get("activity_log") or [])
    log.append(
        {
            "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "text": text,
        }
    )
    st.session_state.activity_log = log[-80:]
