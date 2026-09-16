"""AI Quality Assurance Gate UI Page."""

from __future__ import annotations

import streamlit as st

from qa.evaluator import AIQualityAssuranceAgent


def render_qa_page() -> None:
    st.markdown("## 🛡️ AI Quality Assurance & Compliance Gate")
    st.caption("Inspect 100-point rubric breakdown: Grammar, Fact Consistency, SEO, Copyright, and Readability.")

    agent = AIQualityAssuranceAgent()

    script = st.text_area("Script Content to Audit", value="What if I told you that 82% of creators fail because they do manual video editing? Today we reveal the AI OS framework.")
    title = st.text_input("SEO Title to Audit", value="How to Automate Content Creation using LangGraph AI Agents in 2026")
    threshold = st.slider("Target QA Pass Threshold", min_value=70, max_value=95, value=85)

    if st.button("🔍 Evaluate Content Quality", use_container_width=True):
        report = agent.evaluate(
            master_script={"full_text": script},
            seo_package={"main_title": title},
            threshold=float(threshold),
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overall Quality Score", f"{report.overall_score}/100", f"{'PASSED' if report.passed else 'FAILED'}")
        with col2:
            st.metric("Pass Threshold", f"{report.threshold}/100")

        if report.passed:
            st.success(f"✅ {report.summary_verdict}")
        else:
            st.error(f"❌ {report.summary_verdict}")

        st.divider()

        st.markdown("### 📊 Rubric Score Breakdown")
        b = report.breakdown
        st.write(f"• **Grammar & Style**: {b.grammar_score}/20")
        st.write(f"• **Fact Consistency & Grounding**: {b.fact_consistency_score}/20")
        st.write(f"• **SEO & Discoverability**: {b.seo_score}/20")
        st.write(f"• **Copyright Risk Review**: {b.copyright_risk_score}/20 (Zero Flag Risk)")
        st.write(f"• **Readability & Engagement**: {b.readability_score}/20")

        if report.flagged_issues:
            st.markdown("### ⚠️ Flagged Issues & Fix Suggestions")
            for flag in report.flagged_issues:
                st.warning(f"**[{flag.category}]** {flag.issue}\n\n💡 Suggestion: {flag.suggestion}")
