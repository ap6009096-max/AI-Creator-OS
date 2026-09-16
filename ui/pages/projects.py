"""Projects list from filesystem outputs."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from core.paths import ensure_projects_dir
from ui.session import set_page


def render_projects_page() -> None:
    st.markdown("### Projects")
    root = ensure_projects_dir()
    projects = sorted(
        [p for p in root.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    st.caption(f"{len(projects)} project(s) in `{root}`")

    if not projects:
        st.info("No projects yet. Create a video to generate your first project folder.")
        return

    for proj in projects[:40]:
        meta_path = proj / "project.json"
        title = proj.name
        source = ""
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                source = str(meta.get("source_type") or "")
                title = str(meta.get("project_id") or proj.name)
            except (OSError, json.JSONDecodeError):
                pass
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(f"{source} · `{proj}`")
            if st.button("Open checkpoint", key=f"open_{proj.name}"):
                checkpoint = proj / "checkpoint_plan.json"
                payload = None
                if checkpoint.is_file():
                    try:
                        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        payload = None
                if isinstance(payload, dict):
                    st.session_state.workflow_state = payload
                    st.session_state.project_checkpoint = payload
                    st.session_state.phase = "plan_ready"
                    set_page("plan")
                    st.rerun()
                else:
                    st.warning("No plan checkpoint on disk for this project.")
            export = proj / "exports"
            if export.is_dir() and any(export.iterdir()):
                st.caption("Has exports")
