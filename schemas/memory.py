"""Creator Memory System schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreatorStyleProfile(BaseModel):
    """Style, tone, and hook preferences for a creator."""

    creator_id: str = "default_creator"
    channel_name: str = "My AI Channel"
    niche: str = "Tech & AI"
    target_audience: str = "Creators, Marketers, Developers"
    tone_of_voice: list[str] = Field(
        default_factory=lambda: ["engaging", "authoritative", "witty", "concise"]
    )
    preferred_hooks: list[str] = Field(
        default_factory=lambda: [
            "What if I told you...",
            "Most people get this completely wrong...",
            "Here is the secret nobody talks about...",
        ]
    )
    cta_patterns: list[str] = Field(
        default_factory=lambda: [
            "Subscribe for weekly AI insights!",
            "Drop your thoughts in the comments below.",
            "Click the link to get the free workflow template.",
        ]
    )
    brand_colors: list[str] = Field(
        default_factory=lambda: ["#1E88E5", "#FFC107", "#00E676"]
    )
    forbidden_words: list[str] = Field(
        default_factory=lambda: ["game-changer", "unprecedented", "revolutionary"]
    )
    past_top_topics: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class CreatorMemoryPack(BaseModel):
    profile: CreatorStyleProfile = Field(default_factory=CreatorStyleProfile)
    notes: str = "Loaded from local JSON memory store."


class CreatorMemoryResult(BaseModel):
    memory_pack: CreatorMemoryPack
    memory_path: str
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "creator_memory": self.memory_pack.profile.model_dump(mode="json"),
            "messages": list(self.messages),
        }
