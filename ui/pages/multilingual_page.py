"""Multilingual Content Factory UI Page."""

from __future__ import annotations

import streamlit as st

from multilingual.translator import SUPPORTED_LANGUAGES, MultilingualFactory


def render_multilingual_page() -> None:
    st.markdown("## 🌐 Multilingual Content Factory")
    st.caption("Generate localized scripts, SRT captions, and SEO metadata across 6 major global languages.")

    selected_langs = st.multiselect(
        "Select Target Languages",
        options=list(SUPPORTED_LANGUAGES.keys()),
        default=["en", "hi", "es", "fr", "de", "ar"],
        format_func=lambda x: SUPPORTED_LANGUAGES[x],
    )

    topic = st.text_input("Source Content Title", value="AI Creator OS Multi-Agent Framework")
    script = st.text_area("Source Master Script Snippet", value="Welcome to AI Creator OS. Transform your content production using AI employee teams.")

    if st.button("🌍 Localize Content Package", use_container_width=True):
        factory = MultilingualFactory()
        pack = factory.localize(
            master_script={"full_text": script},
            seo_package={"main_title": topic},
            target_languages=selected_langs,
        )

        st.success(f"Successfully localized into {len(pack.localizations)} languages!")

        for code, loc in pack.localizations.items():
            with st.expander(f"🚩 {loc.language_name} ({code.upper()})"):
                st.markdown(f"**Localized Title:** {loc.translated_title}")
                st.markdown(f"**Localized Script:** {loc.translated_script}")
                st.write("**Localized SEO Tags:**", ", ".join(loc.translated_seo_tags))
                st.code(loc.translated_captions_srt, language="text")
