"""Pipeline page — 7-stage production view + agent activity."""

from __future__ import annotations

from typing import Any

import streamlit as st

from schemas.base import JobStatus
from ui.session import append_activity, set_page
from ui.stage_map import STAGES, agent_card_from_state, stage_statuses_from_state


def _status_icon(status: str) -> str:
    return {
        "completed": "✓",
        "running": "●",
        "failed": "✗",
        "pending": "○",
    }.get(status, "○")


def render_pipeline_checklist(statuses: dict[str, str]) -> None:
    st.markdown("#### AI Production Pipeline")
    lines = []
    for stage in STAGES:
        status = statuses.get(stage.id, "pending")
        icon = _status_icon(status)
        suffix = ""
        if status == "running":
            suffix = "…"
        lines.append(f"{icon} {stage.label}{suffix}")
    st.markdown("\n\n".join(f"- {line}" for line in lines))


def render_agent_card(card: dict[str, Any]) -> None:
    st.markdown("#### Active agent")
    progress = int(card.get("progress") or 0)
    st.markdown(
        f"**{card.get('name', 'Agent')}**  \n"
        f"Status: `{card.get('status')}` · Model: `{card.get('model')}`  \n"
        f"Task: {card.get('task')}"
    )
    st.progress(min(max(progress, 0), 100) / 100.0, text=f"{progress}%")


def render_activity_log() -> None:
    st.markdown("#### Agent Activity")
    log = st.session_state.get("activity_log") or []
    if not log:
        st.caption("Activity will appear as agents run.")
        return
    for row in reversed(log[-20:]):
        st.caption(f"`{row.get('time', '')}`  {row.get('text', '')}")


def render_pipeline_page() -> None:
    """Show pipeline UI and kick off Phase A when a create request is pending."""
    pending = st.session_state.pop("pending_create", None)
    if pending:
        from ui.job_runner import run_plan_phase_from_ui

        append_activity("Supervisor → workflow initialized")
        result = run_plan_phase_from_ui(
            pending["source"],
            pending["config"],
            pending["features"],
        )
        if result and result.get("status") != JobStatus.FAILED.value:
            st.session_state.phase = "plan_ready"
            set_page("plan")
            st.rerun()
        elif result is None or result.get("status") == JobStatus.FAILED.value:
            st.session_state.phase = "failed"

    state = st.session_state.get("workflow_state") or {}
    if state:
        st.session_state.stage_statuses = stage_statuses_from_state(state)
        st.session_state.agent_card = agent_card_from_state(state)

    statuses = st.session_state.get("stage_statuses") or {
        s.id: "pending" for s in STAGES
    }
    left, right = st.columns([1.4, 1])
    with left:
        render_pipeline_checklist(statuses)
        if st.session_state.get("pipeline_error"):
            st.error(st.session_state.pipeline_error)
        phase = st.session_state.get("phase")
        if phase == "plan_ready":
            st.success("Plan ready — review and approve production.")
            if st.button("Open Production Plan", type="primary"):
                set_page("plan")
                st.rerun()
        elif phase == "done":
            st.success("Export completed.")
            if st.button("Open Preview"):
                set_page("preview")
                st.rerun()
        elif phase == "idle":
            st.info("Start from **New Video** to run the production pipeline.")
    with right:
        render_agent_card(st.session_state.get("agent_card") or {})
        render_activity_log()
