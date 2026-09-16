"""Storyboard agent schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoryboardFrame(BaseModel):
    frame_index: int = 0
    clip_id: int = 0
    shot_intent: str = ""
    on_screen_text: str = ""
    narration: str = ""
    duration_hint_sec: float = 3.0
    visual_notes: str = ""


class GeminiStoryboardFrame(BaseModel):
    frame_index: int = 0
    clip_id: int = 0
    shot_intent: str = ""
    on_screen_text: str = ""
    narration: str = ""
    duration_hint_sec: float = 3.0
    visual_notes: str = ""


class GeminiStoryboardBatch(BaseModel):
    frames: list[GeminiStoryboardFrame] = Field(default_factory=list)


class StoryboardReport(BaseModel):
    project_id: str = ""
    frames: list[StoryboardFrame] = Field(default_factory=list)
    provider: str = "gemini-storyboard"
    skipped: bool = False
    notes: str = ""
    created_at: datetime = Field(default_factory=_utc_now)


class StoryboardAgentResult(BaseModel):
    storyboard: StoryboardReport
    storyboard_path: str
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "storyboard": self.storyboard.model_dump(mode="json"),
            "messages": list(self.messages),
        }
