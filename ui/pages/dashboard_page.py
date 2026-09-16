"""Creator Dashboard UI Page — SaaS Metrics & KPIs."""

from __future__ import annotations

import streamlit as st

from dashboard.metrics_calculator import CreatorDashboardCalculator


def render_dashboard_page() -> None:
    st.markdown("## 📊 Creator Dashboard & ROI Metrics")
    st.caption("Track total projects, generated media assets, hours saved, and cost efficiency.")

    calc = CreatorDashboardCalculator()
    metrics = calc.calculate_metrics()

    # Top KPI Metrics Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Projects Created",
            value=metrics.total_projects,
            delta="+100%",
        )

    with col2:
        st.metric(
            label="Videos & Shorts Generated",
            value=f"{metrics.total_videos_generated} Videos / {metrics.total_shorts_generated} Shorts",
            delta=f"{metrics.total_posts_generated} Social Posts",
        )

    with col3:
        st.metric(
            label="Production Hours Saved",
            value=f"{metrics.hours_saved} hrs",
            delta=f"{metrics.efficiency_multiplier}x Faster",
        )

    with col4:
        st.metric(
            label="Est. Cost Savings",
            value=f"${metrics.cost_saved_usd:,.2f}",
            delta="Saved vs Agencies",
        )

    st.divider()

    st.markdown("### ⚡ AI Employee Efficiency & ROI Breakdown")

    left, right = st.columns(2)

    with left:
        st.markdown(
            """
            #### How Savings Are Calculated:
            * **Hours Saved**: Calculated at **8.5 hours** saved per complete multi-channel project package (Research, Scripting, Editing, SEO, Social).
            * **Cost Saved**: Standard market rates: **$350** per long-form video + **$75** per edited vertical Short/Reel.
            * **Multi-Channel Multiplier**: 1 single input produces **6 distinct production formats** simultaneously.
            """
        )

    with right:
        st.markdown("#### Active AI Employee Team")
        employees = [
            ("🧠 AI Researcher", "Topic Intelligence & Fact Extraction"),
            ("🎯 AI Strategist", "Audience Positioning & Hook Design"),
            ("✍️ AI Script Writer", "High-Retention Visual Scripting"),
            ("🎬 AI Director", "Frame-by-Frame Storyboarding"),
            ("✂️ AI Editor", "Audio Sync & Subtitle Rendering"),
            ("🔍 AI SEO Manager", "Keywords & Thumbnail Concepts"),
            ("📱 AI Social Media Manager", "LinkedIn & X Thread Copywriter"),
            ("🛡️ AI QA Agent", "100-Point Quality & Compliance Gate"),
        ]

        for name, role in employees:
            st.markdown(f"**{name}** — *{role}*")
