import streamlit as st

from content_calendar.planner import SmartContentPlanner


def render_calendar_page() -> None:
    st.markdown("## 📅 Smart Content Calendar Planner")
    st.caption("Generate structured 7-day, 30-day, and 90-day publishing strategy schedules.")

    col1, col2 = st.columns(2)
    with col1:
        niche = st.text_input("Creator Niche / Topic", value="AI & Content Automation")
    with col2:
        goal = st.selectbox("Primary Goal", ["Audience Growth", "Brand Authority", "Lead Generation", "Product Sales"])

    planner = SmartContentPlanner()
    pack = planner.plan(niche=niche, goal=goal)

    tab1, tab2, tab3 = st.tabs(["7-Day Sprint Plan", "30-Day Content Roadmap", "90-Day Authority Blueprint"])

    with tab1:
        st.markdown(f"### 🗓️ 7-Day Sprint Plan ({niche})")
        for item in pack.plan_7_day.items:
            st.markdown(
                f"**Day {item.day} ({item.date_label})** — `{item.platform}` ({item.target_time})\n\n"
                f"📌 Title: **{item.content_title}**\n\n"
                f"🏷️ Type: `{item.content_type}` | 💬 Hook: *{item.key_hook}*\n"
            )
            st.divider()

    with tab2:
        st.markdown(f"### 🗓️ 30-Day Content Roadmap ({niche})")
        for item in pack.plan_30_day.items:
            st.markdown(f"**Day {item.day}** — **{item.content_title}** (`{item.platform}`)")

    with tab3:
        st.markdown(f"### 🗓️ 90-Day Authority Blueprint ({niche})")
        for item in pack.plan_90_day.items:
            st.markdown(f"**Day {item.day}** — **{item.content_title}** (`{item.platform}`)")
