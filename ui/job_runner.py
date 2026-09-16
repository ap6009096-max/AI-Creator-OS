"""Build validated jobs from UI input and run LangGraph phases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st
from pydantic import ValidationError

from core.errors import StorageError, VideoAgentError, WorkflowError
from core.logging import get_logger
from core.paths import ensure_uploads_dir
from graph.workflow import (
    run_video_workflow,
    run_video_workflow_from_plan,
    run_video_workflow_until_plan,
)
from schemas.base import JobStatus
from schemas.job import (
    FeatureFlags,
    SourceType,
    VideoJobConfig,
    VideoJobRequest,
    initial_progress_steps,
)
from ui.progress_panel import init_progress_session, update_progress_from_state
from ui.session import append_activity, init_creator_session
from ui.stage_map import (
    activity_lines_from_messages,
    agent_card_from_state,
    stage_statuses_from_state,
)

logger = get_logger(__name__)


def _save_upload(uploaded_file: Any, job_id: str) -> str:
    uploads_dir = ensure_uploads_dir()
    safe_name = Path(uploaded_file.name).name
    dest = uploads_dir / f"{job_id}_{safe_name}"
    try:
        dest.write_bytes(uploaded_file.getbuffer())
    except OSError as exc:
        raise StorageError(f"Failed to save upload: {dest}") from exc
    logger.info("Saved upload to %s", dest)
    return str(dest.resolve())


def build_job_request(
    source: dict[str, Any],
    config: dict[str, Any],
    features: dict[str, Any],
) -> VideoJobRequest:
    job_id = str(uuid4())
    source_type = SourceType(source["source_type"])
    upload_path = ""

    if source_type == SourceType.UPLOAD:
        uploaded = source.get("uploaded_file")
        if uploaded is None:
            raise ValueError("Please upload a video file.")
        upload_path = _save_upload(uploaded, job_id)

    return VideoJobRequest(
        job_id=job_id,
        source_type=source_type,
        youtube_url=source.get("youtube_url") or "",
        local_media_path=source.get("local_media_path") or "",
        upload_path=upload_path,
        script_text=source.get("script_text") or "",
        config=VideoJobConfig(**config),
        features=FeatureFlags(**features),
    )


def _sync_ui_from_state(state: dict[str, Any]) -> None:
    update_progress_from_state(state)
    st.session_state.workflow_state = state
    st.session_state.stage_statuses = stage_statuses_from_state(state)
    st.session_state.agent_card = agent_card_from_state(state)
    for row in activity_lines_from_messages(state.get("messages") or []):
        # Avoid flooding: only append newest message text if not last
        log = st.session_state.get("activity_log") or []
        if not log or log[-1].get("text") != row["text"]:
            append_activity(row["text"])


def _save_checkpoint(state: dict[str, Any]) -> None:
    st.session_state.project_checkpoint = state
    st.session_state.workflow_state = state
    project_dir = state.get("project_dir")
    if not project_dir:
        return
    path = Path(str(project_dir)) / "checkpoint_plan.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not write plan checkpoint: %s", exc)


def _prepare_run(
    source: dict[str, Any],
    config: dict[str, Any],
    features: dict[str, Any],
) -> VideoJobRequest | None:
    init_progress_session()
    init_creator_session()
    try:
        request = build_job_request(source, config, features)
    except (ValueError, ValidationError, VideoAgentError) as exc:
        message = str(exc)
        if isinstance(exc, ValidationError):
            message = "; ".join(err["msg"] for err in exc.errors())
        st.session_state.pipeline_status = JobStatus.FAILED.value
        st.session_state.pipeline_error = message
        st.error(message)
        return None

    st.session_state.job_request = request.model_dump(mode="json")
    st.session_state.pipeline_steps = initial_progress_steps()
    st.session_state.pipeline_status = JobStatus.RUNNING.value
    st.session_state.pipeline_error = None
    st.session_state.last_result = None
    st.session_state.pipeline_messages = []
    st.session_state.activity_log = []
    return request


def run_plan_phase_from_ui(
    source: dict[str, Any],
    config: dict[str, Any],
    features: dict[str, Any],
) -> dict[str, Any] | None:
    """Phase A — understand through storyboard, then checkpoint."""
    request = _prepare_run(source, config, features)
    if request is None:
        return None

    progress_slot = st.empty()

    def _on_step(state: dict[str, Any]) -> None:
        _sync_ui_from_state(state)
        with progress_slot.container():
            from ui.pages.pipeline import (
                render_activity_log,
                render_agent_card,
                render_pipeline_checklist,
            )

            render_pipeline_checklist(st.session_state.stage_statuses)
            render_agent_card(st.session_state.agent_card)
            render_activity_log()

    try:
        with st.spinner("Understanding · researching · planning…"):
            result = run_video_workflow_until_plan(request, on_step=_on_step)
        _sync_ui_from_state(result)
        _save_checkpoint(result)
        progress_slot.empty()
        st.session_state.last_result = result.get("result") or result
        st.session_state.pipeline_status = result.get("status")
        append_activity("Storyboard Agent → plan ready for approval")
        return result
    except WorkflowError as exc:
        progress_slot.empty()
        st.session_state.pipeline_status = JobStatus.FAILED.value
        st.session_state.pipeline_error = str(exc)
        st.error(str(exc))
        return None
    except Exception as exc:  # noqa: BLE001
        progress_slot.empty()
        st.session_state.pipeline_status = JobStatus.FAILED.value
        st.session_state.pipeline_error = f"Unexpected error: {exc}"
        st.error(f"Unexpected error: {exc}")
        logger.exception("Plan phase failed")
        return None


def run_produce_phase_from_ui() -> dict[str, Any] | None:
    """Phase B — produce through export from checkpoint."""
    init_progress_session()
    init_creator_session()
    checkpoint = st.session_state.get("project_checkpoint") or st.session_state.get(
        "workflow_state"
    )
    if not isinstance(checkpoint, dict) or not checkpoint:
        st.error("No plan checkpoint to produce from.")
        return None

    progress_slot = st.empty()
    st.session_state.pipeline_status = JobStatus.RUNNING.value
    st.session_state.pipeline_error = None

    def _on_step(state: dict[str, Any]) -> None:
        _sync_ui_from_state(state)
        with progress_slot.container():
            from ui.pages.pipeline import (
                render_activity_log,
                render_agent_card,
                render_pipeline_checklist,
            )

            render_pipeline_checklist(st.session_state.stage_statuses)
            render_agent_card(st.session_state.agent_card)
            render_activity_log()

    try:
        with st.spinner("Producing · reviewing · exporting…"):
            result = run_video_workflow_from_plan(checkpoint, on_step=_on_step)
        _sync_ui_from_state(result)
        st.session_state.project_checkpoint = result
        progress_slot.empty()
        st.session_state.last_result = result.get("result") or result
        st.session_state.pipeline_status = result.get("status")
        append_activity("Export Agent → package ready")
        return result
    except WorkflowError as exc:
        progress_slot.empty()
        st.session_state.pipeline_status = JobStatus.FAILED.value
        st.session_state.pipeline_error = str(exc)
        st.error(str(exc))
        return None
    except Exception as exc:  # noqa: BLE001
        progress_slot.empty()
        st.session_state.pipeline_status = JobStatus.FAILED.value
        st.session_state.pipeline_error = f"Unexpected error: {exc}"
        st.error(f"Unexpected error: {exc}")
        logger.exception("Produce phase failed")
        return None


def run_job_from_ui(
    source: dict[str, Any],
    config: dict[str, Any],
    features: dict[str, Any],
) -> dict[str, Any] | None:
    """Full end-to-end run (legacy / tests). Prefer plan+produce phases in UI."""
    request = _prepare_run(source, config, features)
    if request is None:
        return None
    progress_slot = st.empty()

    def _on_step(state: dict[str, Any]) -> None:
        _sync_ui_from_state(state)
        with progress_slot.container():
            from ui.progress_panel import render_progress_panel

            render_progress_panel()

    try:
        with st.spinner("Generating video…"):
            result = run_video_workflow(request, on_step=_on_step)
        _sync_ui_from_state(result)
        progress_slot.empty()
        st.session_state.last_result = result.get("result") or result
        return result
    except WorkflowError as exc:
        progress_slot.empty()
        st.session_state.pipeline_status = JobStatus.FAILED.value
        st.session_state.pipeline_error = str(exc)
        st.error(str(exc))
        return None
    except Exception as exc:  # noqa: BLE001
        progress_slot.empty()
        st.session_state.pipeline_status = JobStatus.FAILED.value
        st.session_state.pipeline_error = f"Unexpected error: {exc}"
        st.error(f"Unexpected error: {exc}")
        logger.exception("Unexpected job runner error")
        return None
