"""Preview and export page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from ui.results_panel import render_results_panel
from ui.session import set_page


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def render_preview_page() -> None:
    state = st.session_state.get("workflow_state") or {}
    result = st.session_state.get("last_result") or {}
    if not state and not result:
        st.info("No production yet. Approve a plan or create a new job to produce content.")
        if st.button("➕ Go to Create"):
            set_page("create")
            st.rerun()
        return

    st.markdown("### 🎬 Media Preview & Export Deliverables")
    job = _as_dict(state.get("job") or result.get("job"))
    source_type = str(job.get("source_type") or "script").lower()
    config = _as_dict(job.get("config"))
    export_pack = _as_dict(state.get("export_pack") or result.get("export_pack"))
    render_pack = _as_dict(state.get("render_pack") or result.get("render_pack"))
    plan = _as_dict(render_pack.get("plan"))
    
    video_path = str(
        plan.get("output_path")
        or export_pack.get("export_path")
        or result.get("video_path")
        or ""
    )
    bundle = _as_dict(export_pack.get("bundle"))
    if not video_path or not Path(video_path).is_file():
        video_path = str(bundle.get("video_path") or video_path)

    left, right = st.columns([1.6, 1])
    with left:
        if video_path and Path(video_path).is_file() and video_path.endswith(".mp4"):
            st.video(video_path)
            st.caption(f"📁 Rendered MP4: `{video_path}`")
            with open(video_path, "rb") as f:
                st.download_button(
                    label="📥 Download Rendered MP4 Video",
                    data=f.read(),
                    file_name="final_render.mp4",
                    mime="video/mp4",
                    use_container_width=True,
                )
        elif source_type in {"script", "idea"}:
            st.info(
                "ℹ️ **Script-Only Production Package**\n\n"
                "Master script, visual storyboard, AI employee assets, SEO package, and multi-format copy "
                "were generated successfully. (No video source uploaded for FFmpeg rendering)."
            )
        else:
            render_notes = plan.get("notes") or render_pack.get("notes") or "Media rendering not completed."
            st.warning(
                f"⚠️ **Video Render Status**: {render_notes}\n\n"
                f"Source Type: `{source_type.upper()}`. "
                "If you expected an MP4 video, ensure FFmpeg is installed and the source video file is readable."
            )

        # Scene strip from storyboard
        board = _as_dict(state.get("storyboard"))
        frames = board.get("frames") if isinstance(board.get("frames"), list) else []
        if frames:
            st.markdown("**Scenes & Visual Beats**")
            labels = [
                f"[{i + 1}] {str(f.get('shot_intent') or f.get('on_screen_text') or 'Scene')[:28]}"
                for i, f in enumerate(frames)
                if isinstance(f, dict)
            ]
            st.caption(" · ".join(labels[:12]))

    with right:
        st.markdown("#### Production Configuration")
        st.write(f"**Source Input** · `{source_type.upper()}`")
        st.write(f"**Format Preset** · {config.get('video_type', 'Shorts')}")
        st.write(f"**Language** · {config.get('language', 'English')}")
        st.write(f"**Visual Style** · {config.get('visual_style', 'Cinematic')}")
        st.write(f"**Target Duration** · {config.get('target_clip_duration', '30')} sec")
        st.write(f"**Target Platform** · {config.get('platform', 'YouTube Shorts')}")
        st.write(f"**Captions Burn-in** · {'Enabled' if config.get('caption_burn_in', True) else 'Disabled'}")
        
        project_dir = state.get("project_dir") or result.get("project_dir")
        if project_dir:
            st.caption(f"Project Folder: `{project_dir}`")
            exports = Path(str(project_dir)) / "exports"
            if exports.is_dir():
                st.markdown("**Export Artifacts**")
                for p in sorted(exports.iterdir())[:12]:
                    st.write(f"- `{p.name}`")

    st.divider()
    render_results_panel(result if result else None)
