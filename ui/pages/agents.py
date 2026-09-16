"""Agent Workflow evaluation page."""

from __future__ import annotations

import streamlit as st

from ui.session import set_page
from ui.stage_map import STAGES, stage_statuses_from_state


def render_agents_page() -> None:
    st.markdown("### Agent Workflow")
    st.caption(
        "Evaluation view of the multi-agent Creator Operating System. "
        "Agents collaborate under LangGraph orchestration with Gemini reasoning."
    )

    state = st.session_state.get("workflow_state") or {}
    statuses = stage_statuses_from_state(state) if state else {
        s.id: "pending" for s in STAGES
    }

    cols = st.columns(3)
    clips = (state.get("clips") or {}).get("clips") if isinstance(state.get("clips"), dict) else []
    frames = (state.get("storyboard") or {}).get("frames") if isinstance(state.get("storyboard"), dict) else []
    cols[0].metric("Clips", len(clips) if isinstance(clips, list) else 0)
    cols[1].metric("Scenes", len(frames) if isinstance(frames, list) else 0)
    cols[2].metric("Status", str(state.get("status") or st.session_state.get("phase") or "idle"))

    st.markdown("#### Active workflow")
    chain = " → ".join(
        f"{s.label}({'✓' if statuses.get(s.id) == 'completed' else '●' if statuses.get(s.id) == 'running' else '○'})"
        for s in STAGES
    )
    st.code(chain, language="text")

    st.markdown("#### Agent activity")
    log = st.session_state.get("activity_log") or []
    if not log:
        st.caption("No activity yet.")
    else:
        for row in log[-30:]:
            st.write(f"`{row.get('time')}`  {row.get('text')}")

    if st.button("Back to Create"):
        set_page("create")
        st.rerun()
