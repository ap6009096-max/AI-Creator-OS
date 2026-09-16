"""Production plan checkpoint — content detected + approve gate."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.session import append_activity, set_page


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _content_detected(state: dict[str, Any]) -> dict[str, str]:
    job = _as_dict(state.get("job"))
    config = _as_dict(job.get("config"))
    project = _as_dict(state.get("project"))
    analysis = _as_dict(state.get("analysis"))
    props = _as_dict(analysis.get("properties"))
    clips = _as_dict(state.get("clips"))
    clip_list = clips.get("clips") if isinstance(clips.get("clips"), list) else []

    source = str(project.get("source_type") or job.get("source_type") or "unknown")
    duration = props.get("duration_seconds") or 0
    try:
        duration_f = float(duration or 0)
    except (TypeError, ValueError):
        duration_f = 0.0
    if duration_f <= 0 and clip_list:
        try:
            duration_f = sum(float(c.get("duration") or 0) for c in clip_list if isinstance(c, dict))
        except (TypeError, ValueError):
            duration_f = 0.0

    mins = int(duration_f // 60)
    secs = int(duration_f % 60)
    return {
        "content_type": source.replace("_", " ").title(),
        "purpose": str(config.get("video_type") or "Shorts"),
        "language": str(config.get("language") or "—"),
        "duration": f"{mins}:{secs:02d}" if duration_f else "—",
        "recommended": f"{config.get('target_clip_duration', 60)}-sec {config.get('platform', 'YouTube Shorts')}",
        "style": str(config.get("visual_style") or "—"),
    }


def _plan_blocks(state: dict[str, Any]) -> dict[str, Any]:
    stories = _as_dict(state.get("stories"))
    story_list = stories.get("stories") if isinstance(stories.get("stories"), list) else []
    scripts = _as_dict(state.get("scripts"))
    script_list = scripts.get("scripts") if isinstance(scripts.get("scripts"), list) else []
    board = _as_dict(state.get("storyboard"))
    frames = board.get("frames") if isinstance(board.get("frames"), list) else []

    structure = {}
    if story_list and isinstance(story_list[0], dict):
        structure = _as_dict(story_list[0].get("structure"))
    hook = structure.get("hook") or ""
    if script_list and isinstance(script_list[0], dict):
        hook = hook or str(script_list[0].get("hook") or "")
        title = str(script_list[0].get("title") or "")
    else:
        title = ""

    job = _as_dict(state.get("job"))
    config = _as_dict(job.get("config"))
    return {
        "goal": (
            f"Create a {config.get('target_clip_duration', 60)}-second "
            f"{config.get('language', '')} {config.get('video_type', 'short')}"
        ).strip(),
        "audience": str(config.get("audience") or "General"),
        "style": str(config.get("visual_style") or ""),
        "title": title,
        "hook": hook,
        "context": structure.get("context") or "",
        "value_event": structure.get("value_event") or "",
        "payoff": structure.get("payoff") or "",
        "cta": structure.get("cta") or "",
        "scene_count": len(frames) or len(script_list) or len(story_list),
        "duration": int(config.get("target_clip_duration") or 60),
    }


def render_plan_page() -> None:
    state = st.session_state.get("workflow_state") or {}
    if not state:
        st.info("No plan yet. Create a video to generate an AI Production Plan.")
        if st.button("Go to New Video"):
            set_page("create")
            st.rerun()
        return

    detected = _content_detected(state)
    st.markdown("### Content detected")
    c1, c2, c3 = st.columns(3)
    c1.metric("Content type", detected["content_type"])
    c2.metric("Language", detected["language"])
    c3.metric("Source duration", detected["duration"])
    st.caption(
        f"Purpose: **{detected['purpose']}** · Style: **{detected['style']}** · "
        f"Recommended: **{detected['recommended']}**"
    )

    plan = _plan_blocks(state)
    edits = dict(st.session_state.get("plan_edits") or {})

    st.markdown("### AI Production Plan")
    st.markdown(f"**Goal**  \n{plan['goal']}")
    st.markdown(f"**Audience** · {plan['audience']}  \n**Style** · {plan['style']}")

    st.markdown("**Structure**")
    hook = st.text_area("HOOK", value=edits.get("hook", plan["hook"]), key="plan_hook")
    context = st.text_area(
        "CONTEXT", value=edits.get("context", plan["context"]), key="plan_context"
    )
    insight = st.text_area(
        "KEY INSIGHT",
        value=edits.get("value_event", plan["value_event"]),
        key="plan_insight",
    )
    payoff = st.text_area(
        "PAYOFF", value=edits.get("payoff", plan["payoff"]), key="plan_payoff"
    )
    cta = st.text_area("CTA", value=edits.get("cta", plan["cta"]), key="plan_cta")

    st.caption(
        f"Estimated scenes: **{plan['scene_count']}** · "
        f"Estimated duration: **{plan['duration']} sec**"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Save plan edits", use_container_width=True):
            st.session_state.plan_edits = {
                "hook": hook,
                "context": context,
                "value_event": insight,
                "payoff": payoff,
                "cta": cta,
            }
            # Patch stories in checkpoint for downstream agents
            stories = _as_dict(state.get("stories"))
            story_list = list(stories.get("stories") or [])
            if story_list and isinstance(story_list[0], dict):
                structure = dict(story_list[0].get("structure") or {})
                structure.update(st.session_state.plan_edits)
                story_list[0] = {**story_list[0], "structure": structure}
                stories = {**stories, "stories": story_list}
                state = {**state, "stories": stories}
                st.session_state.workflow_state = state
                st.session_state.project_checkpoint = state
            st.success("Plan edits saved to project checkpoint.")
    with col_b:
        if st.button("Approve & Create", type="primary", use_container_width=True):
            from ui.job_runner import run_produce_phase_from_ui

            append_activity("Supervisor → plan approved, starting production")
            st.session_state.phase = "producing"
            set_page("pipeline")
            result = run_produce_phase_from_ui()
            if result and result.get("status") != "failed":
                st.session_state.phase = "done"
                set_page("preview")
            else:
                st.session_state.phase = "failed"
                set_page("pipeline")
            st.rerun()

    if st.button("View storyboard"):
        set_page("storyboard")
        st.rerun()
