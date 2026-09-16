"""Progress panel for the 15-step generation pipeline."""

from __future__ import annotations

from typing import Any

import streamlit as st

from schemas.base import JobStatus
from schemas.job import PIPELINE_STEPS, ProgressStepStatus, initial_progress_steps


def init_progress_session() -> None:
    """Ensure session state keys used by the progress panel exist."""
    if "pipeline_steps" not in st.session_state:
        st.session_state.pipeline_steps = initial_progress_steps()
    if "pipeline_status" not in st.session_state:
        st.session_state.pipeline_status = JobStatus.PENDING.value
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "pipeline_error" not in st.session_state:
        st.session_state.pipeline_error = None
    if "pipeline_messages" not in st.session_state:
        st.session_state.pipeline_messages = []


def update_progress_from_state(state: dict[str, Any]) -> None:
    """Copy workflow state into Streamlit session for the progress panel."""
    st.session_state.pipeline_steps = state.get("steps", initial_progress_steps())
    st.session_state.pipeline_status = state.get("status", JobStatus.PENDING.value)
    st.session_state.pipeline_error = state.get("error")
    st.session_state.pipeline_messages = state.get("messages", [])
    if state.get("result") is not None:
        st.session_state.last_result = state.get("result")


def _step_icon(status: str) -> str:
    if status == ProgressStepStatus.COMPLETED.value:
        return "✅"
    if status == ProgressStepStatus.RUNNING.value:
        return "🔵"
    if status == ProgressStepStatus.FAILED.value:
        return "❌"
    return "⚪"


def _step_css_class(status: str) -> str:
    return f"ava-step-{status}"


def render_progress_panel() -> None:
    """Render overall progress bar and the 15-step checklist."""
    init_progress_session()
    st.subheader("Progress")

    steps: list[dict[str, Any]] = st.session_state.pipeline_steps
    status = st.session_state.pipeline_status
    total = len(PIPELINE_STEPS) or 15
    completed = sum(
        1 for s in steps if s.get("status") == ProgressStepStatus.COMPLETED.value
    )
    fraction = completed / total if total else 0.0

    st.progress(fraction, text=f"{completed} / {total} steps · status: {status}")

    if st.session_state.pipeline_error:
        st.error(st.session_state.pipeline_error)

    lines: list[str] = ['<div class="ava-progress-card">']
    for step in steps:
        step_status = step.get("status", ProgressStepStatus.PENDING.value)
        icon = _step_icon(step_status)
        css = _step_css_class(step_status)
        label = step.get("label", "")
        idx = step.get("id", 0) + 1
        lines.append(
            f'<div class="{css}">{icon} {idx}. {label}</div>'
        )
    lines.append("</div>")
    st.markdown("\n".join(lines), unsafe_allow_html=True)

    if status == JobStatus.COMPLETED.value:
        st.success("Export completed — pipeline finished successfully.")
        if st.session_state.last_result:
            from ui.results_panel import render_results_panel

            render_results_panel(st.session_state.last_result)
            with st.expander("Raw result JSON"):
                st.json(st.session_state.last_result)
        if st.session_state.pipeline_messages:
            with st.expander("Pipeline messages"):
                for msg in st.session_state.pipeline_messages:
                    st.write(f"- {msg}")
    elif status == JobStatus.FAILED.value and st.session_state.last_result:
        from ui.results_panel import render_results_panel

        render_results_panel(st.session_state.last_result)