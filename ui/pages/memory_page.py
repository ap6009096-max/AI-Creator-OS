"""Creator Memory System UI Page."""

from __future__ import annotations

import json
import streamlit as st

from memory.manager import CreatorMemoryManager
from schemas.memory import CreatorStyleProfile


def render_memory_page() -> None:
    st.markdown("## 🧠 Creator Memory System")
    st.caption("Manage persistent creator profiles, tone of voice, preferred hooks, CTA rules, and visual style.")

    manager = CreatorMemoryManager()
    
    creator_id = st.text_input("Creator ID / Channel Handle", value="default_creator")
    profile = manager.load_profile(creator_id)

    st.divider()

    st.subheader("Edit Style Profile")
    with st.form("memory_form"):
        channel_name = st.text_input("Channel / Brand Name", value=profile.channel_name)
        niche = st.text_input("Niche / Category", value=profile.niche)
        target_audience = st.text_area("Target Audience Persona", value=profile.target_audience)
        
        tone_input = st.text_input("Tone of Voice (comma separated)", value=", ".join(profile.tone_of_voice))
        hooks_input = st.text_area("Preferred Viral Hooks (one per line)", value="\n".join(profile.preferred_hooks))
        cta_input = st.text_area("Call-To-Action Patterns (one per line)", value="\n".join(profile.cta_patterns))
        brand_colors = st.text_input("Brand Colors (hex, comma separated)", value=", ".join(profile.brand_colors))
        forbidden_input = st.text_input("Forbidden Words (comma separated)", value=", ".join(profile.forbidden_words))

        submitted = st.form_submit_button("💾 Save Creator Memory Profile")

        if submitted:
            updated_profile = CreatorStyleProfile(
                creator_id=creator_id,
                channel_name=channel_name,
                niche=niche,
                target_audience=target_audience,
                tone_of_voice=[t.strip() for t in tone_input.split(",") if t.strip()],
                preferred_hooks=[h.strip() for h in hooks_input.split("\n") if h.strip()],
                cta_patterns=[c.strip() for c in cta_input.split("\n") if c.strip()],
                brand_colors=[c.strip() for c in brand_colors.split(",") if c.strip()],
                forbidden_words=[f.strip() for f in forbidden_input.split(",") if f.strip()],
                past_top_topics=profile.past_top_topics,
            )
            saved_path = manager.save_profile(updated_profile)
            st.success(f"Creator Memory saved to `{saved_path}`!")

    st.divider()
    st.subheader("JSON Profile Storage Inspection")
    path = manager._get_path(creator_id)
    if path.exists():
        st.json(json.loads(path.read_text(encoding="utf-8")))
