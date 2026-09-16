"""AI Social Media Manager Employee.

Responsibilities: Platform-native copy drafting for LinkedIn, X/Twitter, Instagram, TikTok.
Inputs: MasterScript, SEOPackage, StrategyPlan.
Outputs: SocialMediaPack.
"""

from __future__ import annotations

from typing import Any

from core.logging import get_logger
from schemas.employees import SocialMediaPack

logger = get_logger(__name__)


class AISocialMediaManager:
    """AI Social Media Manager Node in LangGraph workflow."""

    def run(
        self,
        master_script: dict[str, Any] | None = None,
        seo_package: dict[str, Any] | None = None,
        content_strategy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info("AI Social Media Manager drafting platform-specific post assets...")

        topic = (seo_package or {}).get("main_title", "AI Content Production Operating System")
        hook = (master_script or {}).get("hook_selected", "What if you could automate your entire media workflow?")

        linkedin_post = (
            f"🚀 {hook}\n\n"
            f"Most creators spend 15+ hours every week juggling research, scripting, editing, and SEO formatting.\n\n"
            f"We built an AI Employee Team powered by LangGraph to handle the heavy lifting:\n"
            f"1️⃣ AI Researcher: Topic intelligence & stats\n"
            f"2️⃣ AI Strategist: Target positioning & hooks\n"
            f"3️⃣ AI Script Writer: High-retention narrative\n"
            f"4️⃣ AI Director: Frame-by-frame visual storyboard\n"
            f"5️⃣ AI Editor: Audio sync & dynamic rendering\n"
            f"6️⃣ AI SEO & Social Managers: Multi-channel distribution\n\n"
            f"The result? 8.5 hours saved per project and 340% wider distribution reach.\n\n"
            f"What's your biggest bottleneck in content creation? Drop a comment below!👇\n\n"
            f"#AICreatorOS #ArtificialIntelligence #ContentMarketing #Automation"
        )

        x_thread = [
            f"1/ {hook}\n\nHere is how an AI Employee Team automates full-stack content creation in 2026 🧵👇",
            f"2/ Step 1: Viral Research\nAI Researcher scans search trends, extracts key facts, and identifies high-retention content pillars.",
            f"3/ Step 2: High-Retention Scripting\nAI Script Writer uses pattern-interrupt hooks and timed visual cues to keep watch time above 70%.",
            f"4/ Step 3: Multi-Format Repurposing\nFrom 1 master video, the platform generates 3 Shorts, a LinkedIn breakdown, an X thread, and a blog post automatically.",
            f"5/ If you found this useful, RT the first tweet and follow for daily AI production blueprints! 🔁",
        ]

        instagram_caption = (
            f"Transform ideas into production-ready content packages on autopilot ⚡\n\n"
            f"💡 Topic: {topic}\n"
            f"🎯 Multi-Agent AI Employee Workflow\n\n"
            f"Save this post & check out the link in bio for the full framework breakdown! 🔥\n\n"
            f"#AIReels #CreatorTools #ContentOS #VideoAutomation #GrowthHacking"
        )

        tiktok_caption = f"How to 10x your video output using AI agents 🤖⚡ #AICreatorOS #ContentCreator #AITools #TechTok"

        social_pack = SocialMediaPack(
            linkedin_post=linkedin_post,
            x_thread=x_thread,
            instagram_caption=instagram_caption,
            tiktok_caption=tiktok_caption,
        )

        return {
            "social_media_pack": social_pack.model_dump(mode="json"),
            "messages": [f"[ai_social_media_manager] Generated LinkedIn post, 5-part X thread, Instagram Reel caption, and TikTok copy."],
        }
