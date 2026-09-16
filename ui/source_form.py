"""Source selector and input widgets."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.constants import ALLOWED_UPLOAD_TYPES, SOURCE_LABEL_TO_TYPE, SOURCE_OPTIONS


def render_source_form() -> dict[str, Any]:
    """Render SOURCE controls and return raw UI values (not yet validated)."""
    st.subheader("SOURCE")
    source_label = st.radio(
        "Input method",
        options=SOURCE_OPTIONS,
        horizontal=True,
        label_visibility="collapsed",
    )
    source_type = SOURCE_LABEL_TO_TYPE[source_label]

    youtube_url = ""
    uploaded_file = None
    script_text = ""

    if source_type == "youtube":
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=…",
            help="Paste a public YouTube video link.",
        )
    elif source_type == "upload":
        uploaded_file = st.file_uploader(
            "Upload video",
            type=ALLOWED_UPLOAD_TYPES,
            help="MP4, MOV, AVI, MKV, or WebM.",
        )
    else:
        script_text = st.text_area(
            "Text / Script",
            height=160,
            placeholder="Paste or write the script for your video…",
        )

    return {
        "source_type": source_type,
        "youtube_url": youtube_url,
        "uploaded_file": uploaded_file,
        "script_text": script_text,
    }
