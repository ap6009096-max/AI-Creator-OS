"""AI Strategist Employee.

Responsibilities: Content positioning, platform adaptation, pacing strategy, CTA placement.
Inputs: ResearchBrief, CreatorMemory, ViralIntelligence.
Outputs: Structured StrategyPlan.
"""

from __future__ import annotations

from typing import Any

from core.logging import get_logger
from schemas.employees import StrategyPlan
from schemas.memory import CreatorStyleProfile

logger = get_logger(__name__)


class AIStrategist:
    """AI Strategist Node in LangGraph workflow."""

    def run(
        self,
        research_brief: dict[str, Any] | None = None,
        creator_memory: dict[str, Any] | None = None,
        viral_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info("AI Strategist formulating content plan...")

        profile = CreatorStyleProfile.model_validate(creator_memory) if creator_memory else CreatorStyleProfile()
        topic = (research_brief or {}).get("core_topic", "AI Production")

        selected_hook = "Contrarian Pattern Interrupt"
        if viral_analysis and isinstance(viral_analysis, dict):
            hooks = viral_analysis.get("viral_hooks", [])
            if hooks and len(hooks) > 0:
                selected_hook = hooks[0].get("hook_text", selected_hook)

        plan = StrategyPlan(
            content_angle=f"High-Impact Blueprint for {topic} targeting {profile.target_audience}",
            pacing_style="Fast-Paced with dynamic visual cuts every 2-3 seconds",
            visual_theme="SaaS Dark Aesthetic with Electric Blue accents",
            hook_strategy=selected_hook,
            target_platforms=["YouTube", "LinkedIn", "X", "Instagram Reels"],
            call_to_action=profile.cta_patterns[0] if profile.cta_patterns else "Subscribe for more AI insights!",
        )

        return {
            "content_strategy": plan.model_dump(mode="json"),
            "messages": [f"[ai_strategist] Strategy formulated: '{plan.content_angle}' with hook '{plan.hook_strategy[:40]}...'."],
        }
