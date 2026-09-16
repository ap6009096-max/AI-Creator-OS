"""Content Repurposing & Multi-Channel Export Page."""

from __future__ import annotations

import streamlit as st

from repurposing.engine import ContentRepurposingEngine


def render_repurpose_page() -> None:
    st.markdown("## 📦 Content Repurposing & Download Center")
    st.caption("Inspect and download multi-channel production packages generated from a single source.")

    engine = ContentRepurposingEngine()
    
    topic = st.text_input("Source Topic / Video Title", value="AI Creator OS Launch")

    if st.button("✨ Generate Multi-Channel Repurposed Assets", use_container_width=True):
        with st.spinner("Generating Long-form, Shorts clips, Blog Article, LinkedIn, X Thread, and SRT..."):
            pkg = engine.generate_package(
                project_id="demo_project",
                master_script={"title": topic, "full_text": "Welcome to AI Creator OS. Automating media workflows."},
            )

            tabs = st.tabs([
                "🎥 Vertical Shorts",
                "📝 Blog Article (MD)",
                "💼 LinkedIn Post",
                "🐦 X Thread",
                "💬 SRT Captions",
                "🔍 SEO Package",
            ])

            with tabs[0]:
                st.markdown("### 🎬 3 Generated Short Clips")
                for s in pkg.shorts_clips:
                    st.subheader(f"[{s.clip_id}] {s.title}")
                    st.caption(f"Time Range: {s.start_time} - {s.end_time} | Aspect Ratio: {s.vertical_aspect}")
                    st.code(f"Hook: {s.hook}\nSnippet: {s.transcript_snippet}")
                    st.download_button(f"📥 Download {s.clip_id} Script & Timestamps", s.model_dump_json(indent=2), file_name=f"{s.clip_id}.json")

            with tabs[1]:
                st.markdown("### 📝 Markdown Blog Article")
                st.markdown(pkg.blog_article_md)
                st.download_button("📥 Download Article (.md)", pkg.blog_article_md, file_name="article.md")

            with tabs[2]:
                st.markdown("### 💼 LinkedIn Thought Leadership Post")
                st.text_area("LinkedIn Post Copy", pkg.social_media.linkedin_post, height=300)

            with tabs[3]:
                st.markdown("### 🐦 X (Twitter) Multi-Tweet Thread")
                for idx, tweet in enumerate(pkg.social_media.x_thread, 1):
                    st.code(tweet, language="markdown")

            with tabs[4]:
                st.markdown("### 💬 SRT Subtitles")
                st.code(pkg.captions_srt, language="text")
                st.download_button("📥 Download Subtitles (.srt)", pkg.captions_srt, file_name="subtitles.srt")

            with tabs[5]:
                st.markdown("### 🔍 SEO Package")
                st.write("**Main Title:**", pkg.seo_package.main_title)
                st.write("**Keywords:**", ", ".join(pkg.seo_package.primary_keywords))
                st.write("**Thumbnail Concepts:**")
                for thumb in pkg.seo_package.thumbnail_text_concepts:
                    st.info(f"🖼️ {thumb}")
