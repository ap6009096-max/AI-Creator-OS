"""Prompts for Storyboard Agent."""

from __future__ import annotations

STORYBOARD_AGENT_SYSTEM = """You create ordered storyboard frames for short-form video.
Each frame needs shot_intent, on_screen_text, narration, duration_hint_sec, and visual_notes.
Keep frames practical for editing; align clip_id with provided scripts when possible."""


def build_storyboard_agent_user_prompt(
    *,
    script_blocks: list[str],
    story_blocks: list[str] | None = None,
    video_type: str = "Shorts",
) -> str:
    scripts = "\n\n".join(script_blocks) if script_blocks else "(no scripts)"
    stories = "\n\n".join(story_blocks or []) or "(no stories)"
    return (
        f"Video type: {video_type}\n\n"
        f"Scripts:\n{scripts}\n\n"
        f"Stories:\n{stories}\n\n"
        "Return an ordered list of storyboard frames."
    )
