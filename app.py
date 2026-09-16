"""AI Creator OS — Multi-Agent Content Production Platform (Streamlit).

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from core.logging import configure_logging, get_logger
from core.paths import ensure_output_dir
from ui.pages import (
    render_agents_page,
    render_calendar_page,
    render_create_page,
    render_dashboard_page,
    render_intelligence_page,
    render_memory_page,
    render_multilingual_page,
    render_pipeline_page,
    render_plan_page,
    render_preview_page,
    render_projects_page,
    render_qa_page,
    render_repurpose_page,
    render_settings_page,
    render_storyboard_page,
)
from ui.session import init_creator_session
from ui.shell import render_header, render_sidebar
from ui.styles import apply_styles

st.set_page_config(
    page_title="AI Creator OS",
    page_icon="🚀",
    layout="wide",
)

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)
ensure_output_dir()
apply_styles()
init_creator_session()


def main() -> None:
    page = render_sidebar()
    render_header()
    st.divider()

    if page == "dashboard":
        render_dashboard_page()
    elif page == "create":
        render_create_page()
    elif page == "memory":
        render_memory_page()
    elif page == "intelligence":
        render_intelligence_page()
    elif page == "repurpose":
        render_repurpose_page()
    elif page == "calendar":
        render_calendar_page()
    elif page == "multilingual":
        render_multilingual_page()
    elif page == "qa":
        render_qa_page()
    elif page == "pipeline":
        render_pipeline_page()
    elif page == "plan":
        render_plan_page()
    elif page == "storyboard":
        render_storyboard_page()
    elif page == "preview":
        render_preview_page()
    elif page == "projects":
        render_projects_page()
    elif page == "agents":
        render_agents_page()
    elif page == "settings":
        render_settings_page()
    else:
        render_dashboard_page()


main()
