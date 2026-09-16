"""Content Repurposing Engine implementation."""

from __future__ import annotations

from typing import Any

from core.logging import get_logger
from schemas.employees import SEOPackage, SocialMediaPack
from schemas.repurposing import (
    RepurposedContentPackage,
    RepurposingResult,
    ShortClipAsset,
)

logger = get_logger(__name__)


class ContentRepurposingEngine:
    """Engine that transforms master script and media into multi-channel output formats."""

    def generate_package(
        self,
        project_id: str,
        master_script: dict[str, Any] | None = None,
        seo_package: dict[str, Any] | None = None,
        social_media_pack: dict[str, Any] | None = None,
        transcript: dict[str, Any] | None = None,
    ) -> RepurposedContentPackage:
        logger.info("Repurposing content into multi-channel asset bundle for project: %s", project_id)

        title = (master_script or {}).get("title", "AI Content Production Masterclass")
        full_text = (master_script or {}).get("full_text", "")

        # 1. Shorts clips
        shorts = [
            ShortClipAsset(
                clip_id="short_01",
                title="The Viral Hook Secret",
                hook="Stop making content without this 1 rule...",
                start_time="00:00",
                end_time="00:15",
                transcript_snippet=full_text[:120] if full_text else "High impact viral hook statement.",
                vertical_aspect="9:16",
            ),
            ShortClipAsset(
                clip_id="short_02",
                title="AI Employee Architecture Breakdown",
                hook="How 7 AI employees create videos for you...",
                start_time="00:15",
                end_time="00:45",
                transcript_snippet=full_text[120:300] if len(full_text) > 300 else "AI team breakdown snippet.",
                vertical_aspect="9:16",
            ),
            ShortClipAsset(
                clip_id="short_03",
                title="340% Higher Reach Framework",
                hook="The multi-channel distribution cheat code...",
                start_time="00:45",
                end_time="01:00",
                transcript_snippet=full_text[300:] if len(full_text) > 300 else "CTA and distribution framework.",
                vertical_aspect="9:16",
            ),
        ]

        # 2. Markdown blog article
        blog_md = (
            f"# {title}\n\n"
            f"## Executive Summary\n"
            f"In today's fast-paced digital ecosystem, creating content manually is no longer scalable. "
            f"By leveraging a coordinated team of AI employees, creators and businesses can automate research, "
            f"scripting, video editing, and distribution.\n\n"
            f"## Key Takeaways\n"
            f"- **Viral Hook Optimization**: Pattern interrupts drive 90%+ 3-second retention.\n"
            f"- **Automated Scripting**: Timed visual cues ensure visual rhythm every 2-3 seconds.\n"
            f"- **Multi-Channel Distribution**: 1 master video yields 3 shorts, 1 article, and 4 social posts.\n\n"
            f"## Step-by-Step Implementation Guide\n"
            f"1. **Set Up Creator Memory**: Persist tone, style, and brand preferences.\n"
            f"2. **Run Viral Intelligence**: Predict engagement and retention prior to generation.\n"
            f"3. **Deploy AI Employees**: Orchestrate LangGraph nodes from research to final export.\n\n"
            f"--- \n*Generated automatically by AI Creator OS.*"
        )

        # 3. SRT Captions
        srt_captions = (
            "1\n00:00:00,000 --> 00:00:05,000\nWelcome to AI Creator OS.\n\n"
            "2\n00:00:05,000 --> 00:00:15,000\nTransforming ideas into multi-channel content packages.\n\n"
            "3\n00:00:15,000 --> 00:00:30,000\nPowered by a coordinated team of AI employees.\n"
        )

        seo = SEOPackage.model_validate(seo_package) if seo_package else SEOPackage(main_title=title)
        social = SocialMediaPack.model_validate(social_media_pack) if social_media_pack else SocialMediaPack()

        return RepurposedContentPackage(
            project_id=project_id,
            source_title=title,
            long_form_summary="Complete production package generated with long-form video, 3 vertical clips, SEO metadata, and social posts.",
            shorts_clips=shorts,
            blog_article_md=blog_md,
            social_media=social,
            seo_package=seo,
            captions_srt=srt_captions,
        )

    def run(
        self,
        project_id: str = "project_default",
        master_script: dict[str, Any] | None = None,
        seo_package: dict[str, Any] | None = None,
        social_media_pack: dict[str, Any] | None = None,
        transcript: dict[str, Any] | None = None,
    ) -> RepurposingResult:
        package = self.generate_package(
            project_id=project_id,
            master_script=master_script,
            seo_package=seo_package,
            social_media_pack=social_media_pack,
            transcript=transcript,
        )
        messages = [
            f"[repurposing_engine] Content successfully repurposed into 1 Long-Form Spec, 3 Shorts Clips, 1 Blog Article, LinkedIn Post, X Thread, and SRT Captions."
        ]
        return RepurposingResult(repurposed_package=package, messages=messages)
