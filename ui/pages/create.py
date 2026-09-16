"""Create page — primary creator input."""

from __future__ import annotations

from typing import Any

import streamlit as st

from schemas.job import FeatureFlags
from ui.config_form import render_config_form
from ui.constants import (
    ALLOWED_UPLOAD_TYPES,
    LANGUAGES,
    TARGET_CLIP_DURATIONS,
    VIDEO_TYPES,
    VISUAL_STYLES,
)
from ui.feature_toggles import render_feature_toggles
from ui.session import set_page

CREATE_MODES = ("YouTube", "Upload", "Script", "Idea")


def render_create_page() -> None:
    """Creator-first home: one primary input + quick settings."""
    st.markdown("### What do you want to create?")

    mode = st.radio(
        "Input mode",
        CREATE_MODES,
        horizontal=True,
        label_visibility="collapsed",
        key="create_mode",
    )

    youtube_url = ""
    local_media_path = ""
    uploaded_file = None
    script_text = ""

    if mode == "YouTube":
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=…",
            key="create_youtube_url",
        )
        local_media_path = st.text_input(
            "Authorized local media path (optional)",
            placeholder=r"C:\path\to\video.mp4",
            help=(
                "Use this when you already have permission to access a local copy. "
                "Without it, YouTube metadata cannot be transcribed."
            ),
            key="create_local_media_path",
        ).strip()
    elif mode == "Upload":
        uploaded_file = st.file_uploader(
            "Drop video / audio here",
            type=ALLOWED_UPLOAD_TYPES,
            key="create_upload",
        )
    elif mode == "Script":
        script_text = st.text_area(
            "Script",
            height=140,
            placeholder="Paste your full script…",
            key="create_script",
        )
    else:
        script_text = st.text_area(
            "Describe your idea",
            height=140,
            placeholder="Create a motivational story about…",
            key="create_idea",
        )

    instructions = st.text_area(
        "Story / Instructions",
        height=90,
        placeholder='e.g. "Turn this into a 60-second Hindi reel…"',
        key="create_instructions",
    )

    st.markdown("#### Quick settings")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        video_type = st.selectbox(
            "Format",
            VIDEO_TYPES,
            index=VIDEO_TYPES.index("Shorts") if "Shorts" in VIDEO_TYPES else 0,
            key="quick_format",
        )
    with q2:
        language = st.selectbox(
            "Language",
            LANGUAGES,
            index=LANGUAGES.index("Hindi") if "Hindi" in LANGUAGES else 0,
            key="quick_language",
        )
    with q3:
        visual_style = st.selectbox(
            "Style",
            VISUAL_STYLES,
            index=VISUAL_STYLES.index("Cinematic") if "Cinematic" in VISUAL_STYLES else 0,
            key="quick_style",
        )
    with q4:
        duration = st.selectbox(
            "Duration",
            TARGET_CLIP_DURATIONS,
            index=TARGET_CLIP_DURATIONS.index(60)
            if 60 in TARGET_CLIP_DURATIONS
            else TARGET_CLIP_DURATIONS.index(30),
            key="quick_duration",
        )

    with st.expander("Advanced Settings", expanded=False):
        advanced_config = render_config_form()
        features = render_feature_toggles()

    # Quick settings win for the four primary creator fields
    config: dict[str, Any] = {
        **advanced_config,
        "video_type": video_type,
        "language": language,
        "visual_style": visual_style,
        "target_clip_duration": int(duration),
    }
    if not isinstance(features, dict):
        features = FeatureFlags().model_dump(mode="json")

    if instructions.strip() and mode in {"Script", "Idea"}:
        script_text = (
            f"{script_text.strip()}\n\n[Instructions]\n{instructions.strip()}"
        ).strip()
    elif instructions.strip():
        st.session_state["create_extra_instructions"] = instructions.strip()

    create = st.button("Create Video", type="primary", use_container_width=True)
    if not create:
        return

    if mode == "YouTube":
        source_type = "youtube"
        if not youtube_url.strip():
            st.error("Paste a YouTube URL to continue.")
            return
    elif mode == "Upload":
        source_type = "upload"
        if uploaded_file is None:
            st.error("Upload a media file to continue.")
            return
    else:
        source_type = "script"
        if not script_text.strip():
            st.error("Add a script or idea to continue.")
            return

    source = {
        "source_type": source_type,
        "youtube_url": youtube_url,
        "local_media_path": local_media_path,
        "uploaded_file": uploaded_file,
        "script_text": script_text,
    }

    # ── Auto-run Phase A (understand → plan → storyboard) inline ──────────
    # This means pressing "Create Video" drives the full plan phase without
    # the user needing to understand the two-phase internal split.
    from ui.job_runner import run_plan_phase_from_ui  # local import avoids circular
    from ui.session import append_activity

    append_activity("Supervisor → workflow initialized")
    with st.spinner("🤖 AI Crew working… researching · planning · storyboarding…"):
        result = run_plan_phase_from_ui(source, config, features)

    if result and result.get("status") != "failed":
        st.session_state.phase = "plan_ready"
        set_page("plan")
    else:
        # Keep pending payload so pipeline page can show the error state
        st.session_state["pending_create"] = {
            "source": source,
            "config": config,
            "features": features,
            "instructions": instructions.strip(),
        }
        set_page("pipeline")
    st.rerun()
