"""App chrome: sidebar navigation, header, system status."""

from __future__ import annotations

import shutil

import streamlit as st

from config.settings import get_settings
from ui.session import NAV_PAGES, init_creator_session, set_page


def render_system_status() -> None:
    """Bottom / sidebar readiness indicators."""
    settings = get_settings()
    ffmpeg_ok = bool(settings.ffmpeg_path.strip()) or bool(shutil.which("ffmpeg"))
    bits = [
        ("Gemini", settings.has_gemini_api_key),
        ("Parallel Search", settings.has_parallel_api_key),
        ("FFmpeg", ffmpeg_ok),
    ]
    parts = []
    for label, ok in bits:
        mark = "●" if ok else "○"
        parts.append(f"{mark} {label}")
    st.caption("  ·  ".join(parts) + "  ·  LangGraph Ready")


def render_header() -> None:
    left, right = st.columns([4, 1])
    with left:
        st.markdown("## 🚀 AI Creator OS")
        st.caption(
            "Multi-Agent Content Production Platform — transforming ideas, videos, podcasts, "
            "and scripts into complete production-ready packages using a coordinated team of AI employees."
        )
    with right:
        settings = get_settings()
        ready = settings.has_gemini_api_key
        st.markdown(
            f"<div style='text-align:right;padding-top:0.75rem;'>"
            f"<span style='color:{'#059669' if ready else '#b45309'};font-weight:600;'>"
            f"{'● AI Employees Ready' if ready else '○ Configure Gemini'}</span></div>",
            unsafe_allow_html=True,
        )
    st.caption("Memory · Intelligence · AI Employees · Repurposing · QA Gate · Multilingual")


def render_sidebar() -> str:
    """Render creator sidebar; return selected page id."""
    init_creator_session()
    settings = get_settings()

    st.sidebar.markdown("### 🎬 AI Creator OS")
    st.sidebar.caption("Content Production Operating System")

    st.sidebar.markdown("**CREATE**")
    if st.sidebar.button("➕ New Content Package", use_container_width=True):
        set_page("create")

    st.sidebar.markdown("**WORKSPACE**")
    for page_id, label in NAV_PAGES:
        if page_id in {"create", "settings"}:
            continue
        if st.sidebar.button(label, key=f"nav_{page_id}", use_container_width=True):
            set_page(page_id)

    st.sidebar.markdown("**SYSTEM**")
    if st.sidebar.button("Settings", key="nav_settings", use_container_width=True):
        set_page("settings")

    st.sidebar.divider()
    st.sidebar.markdown("**🤖 AI Employee Team**")
    for name in (
        "AI Supervisor",
        "AI Researcher",
        "AI Strategist",
        "AI Script Writer",
        "AI Director",
        "AI Editor",
        "AI SEO Manager",
        "AI Social Media Manager",
        "AI QA Agent",
    ):
        st.sidebar.caption(f"● {name}")

    st.sidebar.divider()
    render_system_status()
    st.sidebar.caption(f"Env: `{settings.app_env}`")
    return str(st.session_state.get("nav_page") or "dashboard")
