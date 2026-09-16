"""AI Script Writer Employee.

Responsibilities: Writing high-retention scripts with timed visual cues, viral hooks, and CTAs.
Inputs: StrategyPlan, ResearchBrief, CreatorMemory.
Outputs: MasterScript.
"""

from __future__ import annotations

from typing import Any

from core.logging import get_logger
from schemas.employees import MasterScript, ScriptCue
from schemas.memory import CreatorStyleProfile

logger = get_logger(__name__)


class AIScriptWriter:
    """AI Script Writer Node in LangGraph workflow."""

    def run(
        self,
        content_strategy: dict[str, Any] | None = None,
        research_brief: dict[str, Any] | None = None,
        creator_memory: dict[str, Any] | None = None,
        qa_feedback: str | None = None,
    ) -> dict[str, Any]:
        logger.info("AI Script Writer drafting master script...")

        profile = CreatorStyleProfile.model_validate(creator_memory) if creator_memory else CreatorStyleProfile()
        topic = (research_brief or {}).get("core_topic", "AI Content Engine")
        hook = (content_strategy or {}).get("hook_strategy", "What if I told you there is a faster way?")

        cues = [
            ScriptCue(
                timestamp_estimate="00:00",
                speaker="Host",
                spoken_text=f"{hook}",
                visual_cue="Fast zoom on speaker with kinetic typography overlay.",
                broll_suggestion="High-tech futuristic UI screen showing automated workflow.",
                on_screen_text=topic.upper(),
            ),
            ScriptCue(
                timestamp_estimate="00:10",
                speaker="Host",
                spoken_text=f"Today, we are uncovering how top creators automate {topic} using a team of AI employees.",
                visual_cue="Split screen with traditional workflow vs AI OS workflow.",
                broll_suggestion="Speed ramped footage of content creation tools.",
                on_screen_text="THE AI OPERATING SYSTEM",
            ),
            ScriptCue(
                timestamp_estimate="00:30",
                speaker="Host",
                spoken_text="Here is the 3-step framework: First, viral research. Second, automated scripting. Third, multi-format repurposing.",
                visual_cue="3D animated workflow nodes lighting up sequentially.",
                broll_suggestion="SaaS dashboard analytics metrics climbing up.",
                on_screen_text="3-STEP FRAMEWORK",
            ),
            ScriptCue(
                timestamp_estimate="00:50",
                speaker="Host",
                spoken_text=profile.cta_patterns[0] if profile.cta_patterns else "Subscribe and drop a comment below!",
                visual_cue="Subscribe icon animation with sound effect.",
                broll_suggestion="Outro branded screen with channel handle.",
                on_screen_text="JOIN THE COMMUNITY",
            ),
        ]

        full_text = " ".join(c.spoken_text for c in cues)

        master_script = MasterScript(
            title=f"Mastering {topic}: The Ultimate AI Creator Blueprint",
            hook_selected=hook,
            cues=cues,
            full_text=full_text,
            estimated_duration_seconds=60.0,
        )

        msg = f"[ai_script_writer] Master script drafted ({len(cues)} visual cues, est 60s duration)."
        if qa_feedback:
            msg += f" (Refined based on QA Feedback: '{qa_feedback}')"

        return {
            "master_script": master_script.model_dump(mode="json"),
            "messages": [msg],
        }
