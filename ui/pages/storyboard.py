"""Storyboard scene cards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from ui.session import set_page


def _frames_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    board = state.get("storyboard") if isinstance(state.get("storyboard"), dict) else {}
    frames = board.get("frames") if isinstance(board.get("frames"), list) else []
    if frames:
        return [f for f in frames if isinstance(f, dict)]
    scripts = state.get("scripts") if isinstance(state.get("scripts"), dict) else {}
    script_list = scripts.get("scripts") if isinstance(scripts.get("scripts"), list) else []
    out: list[dict[str, Any]] = []
    t = 0.0
    for i, s in enumerate(script_list):
        if not isinstance(s, dict):
            continue
        dur = 7.0
        out.append(
            {
                "frame_index": i,
                "clip_id": s.get("clip_id", i),
                "shot_intent": s.get("title") or "Scene",
                "on_screen_text": s.get("thumbnail_text") or s.get("hook") or "",
                "narration": s.get("short_script") or s.get("hook") or "",
                "duration_hint_sec": dur,
                "visual_notes": "",
                "_start": t,
                "_end": t + dur,
            }
        )
        t += dur
    return out


def _auto_run_plan_phase(pending: dict) -> bool:
    """Run Phase A inline and return True if storyboard frames were produced."""
    from ui.job_runner import run_plan_phase_from_ui
    from ui.session import append_activity

    append_activity("Supervisor → workflow initialized (from Storyboard tab)")
    result = run_plan_phase_from_ui(
        pending["source"],
        pending["config"],
        pending["features"],
    )
    if result and result.get("status") != "failed":
        st.session_state.phase = "plan_ready"
        return True
    return False


def _checkpoint_to_pending(checkpoint: dict[str, Any]) -> dict[str, Any] | None:
    """Recover a pending create payload from an existing checkpoint for auto-recovery."""
    if not isinstance(checkpoint, dict):
        return None

    job = checkpoint.get("job") if isinstance(checkpoint.get("job"), dict) else {}
    if not job:
        job = checkpoint.get("result") if isinstance(checkpoint.get("result"), dict) else {}
    if not isinstance(job, dict):
        return None

    source_type = str(job.get("source_type") or "script")
    source = {
        "source_type": source_type,
        "youtube_url": job.get("youtube_url") or "",
        "local_media_path": job.get("local_media_path") or "",
        "uploaded_file": None,
        "script_text": job.get("script_text") or "",
    }
    config = job.get("config") if isinstance(job.get("config"), dict) else {}
    features = job.get("features") if isinstance(job.get("features"), dict) else {}

    if not source["script_text"] and source_type == "script":
        raw = checkpoint.get("raw_text") or checkpoint.get("source_text") or ""
        source["script_text"] = str(raw)

    if not source["script_text"] and source_type == "upload":
        source["script_text"] = ""

    return {
        "source": source,
        "config": config,
        "features": features,
    }


def render_storyboard_page() -> None:
    state = st.session_state.get("workflow_state") or {}
    frames = _frames_from_state(state)

    # ── Smart guard: auto-trigger Phase A when no frames exist yet ───────────
    if not frames:
        pending = st.session_state.get("pending_create")
        checkpoint = st.session_state.get("project_checkpoint")

        if not pending and checkpoint:
            pending = _checkpoint_to_pending(checkpoint)

        if pending:
            # Job configured but Phase A hasn't run yet — run it now silently.
            with st.spinner("🤖 AI Crew working… researching · planning · storyboarding…"):
                success = _auto_run_plan_phase(pending)
            st.session_state.pop("pending_create", None)
            if success:
                state = st.session_state.get("workflow_state") or {}
                frames = _frames_from_state(state)
            if not frames:
                st.error("Planning completed but no storyboard frames were produced. Check logs.")
                if st.button("Back to Create"):
                    set_page("create")
                    st.rerun()
                return
        elif checkpoint:
            st.warning(
                "⚠️ The plan ran but produced no storyboard frames. "
                "You can review the Production Plan or start over."
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Production Plan", type="primary", use_container_width=True):
                    set_page("plan")
                    st.rerun()
            with col2:
                if st.button("Back to Create", use_container_width=True):
                    set_page("create")
                    st.rerun()
            return
        else:
            # No job, no checkpoint — guide user to start fresh.
            st.info(
                "🎬 **No storyboard yet.**  \n"
                "Go to **New Video** to get started — the AI Crew will research, plan, "
                "and storyboard your content automatically in one click."
            )
            if st.button("✨ Create New Video", type="primary"):
                set_page("create")
                st.rerun()
            return

    st.markdown("### Storyboard")
    st.caption(f"{len(frames)} scene(s)")

    edited_frames: list[dict[str, Any]] = []
    t = 0.0
    for i, frame in enumerate(frames):
        start = float(frame.get("_start", t))
        dur = float(frame.get("duration_hint_sec") or 7.0)
        end = float(frame.get("_end", start + dur))
        t = end
        with st.container(border=True):
            st.markdown(f"**SCENE {i + 1:02d}** · `{start:.0f}s – {end:.0f}s`")
            narration = st.text_area(
                "Voiceover",
                value=str(frame.get("narration") or ""),
                key=f"sb_narr_{i}",
                height=80,
            )
            visual = st.text_input(
                "Visual",
                value=str(frame.get("shot_intent") or frame.get("visual_notes") or ""),
                key=f"sb_vis_{i}",
            )
            on_screen = st.text_input(
                "On-screen text",
                value=str(frame.get("on_screen_text") or ""),
                key=f"sb_ost_{i}",
            )
            notes = st.text_input(
                "Camera / notes",
                value=str(frame.get("visual_notes") or ""),
                key=f"sb_notes_{i}",
            )
            edited_frames.append(
                {
                    **frame,
                    "narration": narration,
                    "shot_intent": visual,
                    "on_screen_text": on_screen,
                    "visual_notes": notes,
                    "duration_hint_sec": dur,
                }
            )

    if st.button("Save storyboard edits", type="primary"):
        board = dict(state.get("storyboard") or {})
        board["frames"] = edited_frames
        state = {**state, "storyboard": board}
        st.session_state.workflow_state = state
        st.session_state.project_checkpoint = state
        project_dir = state.get("project_dir")
        if project_dir:
            path = Path(project_dir) / "analysis" / "storyboard.json"
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(board, indent=2), encoding="utf-8")
                st.success(f"Saved `{path}`")
            except OSError as exc:
                st.warning(f"Saved to session only ({exc})")
        else:
            st.success("Saved storyboard to session checkpoint.")

    st.caption("Per-scene regenerate is planned for a later release.")
