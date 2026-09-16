"""Streamlit UI building blocks for the Creator Operating System."""

from ui.config_form import render_config_form
from ui.feature_toggles import render_feature_toggles
from ui.job_runner import (
    run_job_from_ui,
    run_plan_phase_from_ui,
    run_produce_phase_from_ui,
)
from ui.progress_panel import init_progress_session, render_progress_panel
from ui.results_panel import render_results_panel
from ui.shell import render_header, render_sidebar, render_system_status
from ui.source_form import render_source_form
from ui.styles import apply_styles

__all__ = [
    "apply_styles",
    "init_progress_session",
    "render_config_form",
    "render_feature_toggles",
    "render_header",
    "render_progress_panel",
    "render_results_panel",
    "render_sidebar",
    "render_source_form",
    "render_system_status",
    "run_job_from_ui",
    "run_plan_phase_from_ui",
    "run_produce_phase_from_ui",
]
