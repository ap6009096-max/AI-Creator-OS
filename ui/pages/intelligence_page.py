"""Viral Content Intelligence UI Page."""

from __future__ import annotations

import streamlit as st

from intelligence.viral_engine import ViralIntelligenceEngine
from memory.manager import CreatorMemoryManager


def render_intelligence_page() -> None:
    st.markdown("## 🚀 Viral Content Intelligence Lab")
    st.caption("Analyze trends, generate high-impact viral hooks, and predict engagement & retention scores.")

    engine = ViralIntelligenceEngine()
    memory_mgr = CreatorMemoryManager()
    profile = memory_mgr.load_profile("default_creator")

    topic = st.text_input("Enter Topic / Concept to Analyze", value="How AI Agents Are Replacing Traditional Video Editing")

    if st.button("🔥 Run Viral Intelligence Analysis", use_container_width=True):
        with st.spinner("Analyzing viral trends & calculating retention index..."):
            pack = engine.analyze(topic, profile)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Predicted Engagement Score", f"{pack.predicted_engagement_score}/100", "+8.2 vs average")
            with col2:
                st.metric("Predicted Retention Index", f"{pack.predicted_retention_score}/100", "High Watch Time")
            with col3:
                st.metric("Trend Sentiment", pack.trend_sentiment)

            st.divider()

            st.markdown("### 🎯 Generated Viral Hook Options")
            for hook in pack.viral_hooks:
                st.markdown(
                    f"**[{hook.hook_type}]** (Predicted Rating: **{hook.predicted_impact}/100**)\n\n"
                    f"💬 *\"{hook.hook_text}\"*\n\n"
                    f"💡 Rationale: {hook.rationale}\n"
                )
                st.divider()

            st.markdown("### 💡 Pre-Generation Recommendations")
            for rec in pack.pre_generation_recommendations:
                st.info(f"• {rec}")

            st.markdown("### ⏱️ Retention Trigger Map")
            for trig in pack.key_retention_triggers:
                st.write(f"• `{trig}`")
