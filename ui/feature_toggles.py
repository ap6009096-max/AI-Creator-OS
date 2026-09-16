"""Feature toggle checkboxes for the generation pipeline."""

from __future__ import annotations

from typing import Any

import streamlit as st

from schemas.job import FeatureFlags
from schemas.moments import CATEGORY_FLAG_MAP
from ui.constants import FEATURE_TOGGLE_DEFS

_MOMENT_FLAG_KEYS = tuple(CATEGORY_FLAG_MAP.keys())


def render_feature_toggles() -> dict[str, Any]:
    """Render feature toggles and return a FeatureFlags-compatible dict."""
    st.subheader("Features")
    defaults = FeatureFlags().model_dump()
    values: dict[str, bool] = dict(defaults)

    mode = st.radio(
        "Moment detection",
        options=["Find All Moments", "Custom selection"],
        index=0,
        horizontal=True,
        key="moment_detection_mode",
        help="Find All enables every moment category. Custom lets you pick Only Funny, Only Viral, etc.",
    )

    cols = st.columns(4)
    for i, (key, label) in enumerate(FEATURE_TOGGLE_DEFS):
        with cols[i % 4]:
            if key in _MOMENT_FLAG_KEYS and mode == "Find All Moments":
                values[key] = True
                st.checkbox(label, value=True, key=f"feature_{key}", disabled=True)
            else:
                values[key] = st.checkbox(
                    label, value=defaults[key], key=f"feature_{key}"
                )

    if mode == "Find All Moments":
        for key in _MOMENT_FLAG_KEYS:
            values[key] = True

    return values
