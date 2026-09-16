"""Settings page — system + tech stack."""

from __future__ import annotations

import shutil

import streamlit as st

from config.settings import get_settings
from core.paths import get_output_dir


def render_settings_page() -> None:
    st.markdown("### Settings")
    settings = get_settings()
    st.markdown(
        "**AI Creator OS** — an autonomous Creator Operating System that turns "
        "ideas, scripts, podcasts, uploaded media, and supported video sources into "
        "research-grounded, storyboarded, edited, optimized video productions."
    )
    st.markdown(
        "Powered by `Google Cloud Run` · `Gemini` · `Google ADK` · `Parallel Search API` · "
        "`LangGraph` · `LangChain` · `FFmpeg` · `OpenCV` · `Whisper` · `Docker` · `Streamlit`"
    )
    st.divider()
    st.write(f"**Environment:** `{settings.app_env}`")
    st.write(
        f"**Gemini:** {'configured' if settings.has_gemini_api_key else 'missing key'}"
    )
    st.write(
        f"**Parallel Search:** {'configured' if settings.has_parallel_api_key else 'optional / missing'}"
    )
    st.write(f"**Whisper model:** `{settings.whisper_model}`")
    st.write(f"**Gemini model:** `{settings.gemini_model}`")
    ffmpeg_display = settings.ffmpeg_path.strip() or (
        shutil.which("ffmpeg") or "(not found)"
    )
    st.write(f"**FFmpeg:** `{ffmpeg_display}`")
    st.write(f"**Output dir:** `{get_output_dir()}`")
    st.caption("API keys are never displayed. Set them in `.env`.")
