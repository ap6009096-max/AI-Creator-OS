"""Lightweight Streamlit CSS for the Creator Operating System UI."""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }
    h1, h2, h3 {
        letter-spacing: -0.02em;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
    }
    .ava-step-pending { color: #6b7280; }
    .ava-step-running { color: #2563eb; font-weight: 600; }
    .ava-step-completed { color: #059669; }
    .ava-step-failed { color: #dc2626; font-weight: 600; }
    .ava-progress-card {
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 14px;
        padding: 1rem 1.25rem;
        background: linear-gradient(165deg, #f8fafc 0%, #eef2ff 48%, #f8fafc 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] button {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
    }
</style>
"""


def apply_styles() -> None:
    """Inject studio CSS once per run."""
    st.markdown(_CSS, unsafe_allow_html=True)
