"""Prompts for Research Agent query planning."""

from __future__ import annotations

RESEARCH_AGENT_SYSTEM = """You plan web research for short-form video production.
Return a concise objective and exactly 3 diverse keyword search_queries
(3-6 words each). Focus on trends, facts, and audience-relevant context.
Do not invent citations; only propose what to search."""


def build_research_agent_user_prompt(
    *,
    topic_hint: str,
    video_type: str = "Shorts",
    platform: str = "",
    audience: str = "",
    clip_summaries: list[str] | None = None,
) -> str:
    clips = clip_summaries or []
    clip_block = "\n".join(f"- {c}" for c in clips[:8]) or "- (no clips)"
    return (
        f"Video type: {video_type}\n"
        f"Platform: {platform or 'n/a'}\n"
        f"Audience: {audience or 'General'}\n"
        f"Topic / source hint:\n{topic_hint[:2000]}\n\n"
        f"Selected clip summaries:\n{clip_block}\n\n"
        "Produce objective + exactly 3 search_queries."
    )
