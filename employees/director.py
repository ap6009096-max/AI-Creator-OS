"""AI Director Employee.

Responsibilities: Storyboard creation, shot layout, camera movements, scene pacing, B-roll timing.
Inputs: MasterScript, StrategyPlan.
Outputs: DirectorStoryboard.
"""

from __future__ import annotations

from typing import Any

from core.logging import get_logger
from schemas.employees import DirectorScene, DirectorStoryboard

logger = get_logger(__name__)


class AIDirector:
    """AI Director Node in LangGraph workflow."""

    def run(
        self,
        master_script: dict[str, Any] | None = None,
        content_strategy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info("AI Director generating visual storyboard...")

        cues = (master_script or {}).get("cues", [])
        scenes = []

        for idx, cue in enumerate(cues, start=1):
            scenes.append(
                DirectorScene(
                    scene_id=idx,
                    shot_type="Medium Close Up" if idx % 2 == 1 else "Wide Establishing Shot",
                    camera_movement="Fast Push In" if idx == 1 else "Subtle Slow Pan",
                    visual_description=cue.get("visual_cue", "Host speaking into camera with energetic expression."),
                    overlay_graphics=cue.get("on_screen_text", ""),
                    audio_cue="Whoosh sound effect on cut",
                )
            )

        if not scenes:
            scenes = [
                DirectorScene(
                    scene_id=1,
                    shot_type="Medium Close Up",
                    camera_movement="Fast Push In",
                    visual_description="Opening hook frame with dynamic animated subtitle captions.",
                    overlay_graphics="VIRAL HOOK",
                    audio_cue="Whoosh & Impact Sound Effect",
                )
            ]

        storyboard = DirectorStoryboard(
            concept="High-Energy SaaS Explainer with Kinetic Typography",
            scenes=scenes,
            color_palette=["#0F172A", "#3B82F6", "#00E676"],
            editing_rhythm="Pacing: Cut every 2.5 seconds, use glitch transition on key statements.",
        )

        return {
            "director_storyboard": storyboard.model_dump(mode="json"),
            "messages": [f"[ai_director] Storyboard generated with {len(scenes)} directed scenes."],
        }
