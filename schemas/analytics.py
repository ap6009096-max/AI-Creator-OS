"""Analytics agent schemas (post-quality rollup)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnalyticsReport(BaseModel):
    project_id: str = ""
    clip_count: int = 0
    story_count: int = 0
    script_count: int = 0
    storyboard_frame_count: int = 0
    research_result_count: int = 0
    quality_passed: bool | None = None
    quality_skipped: bool = False
    render_skipped: bool = False
    platform: str = ""
    localization_language: str = ""
    localization_country: str = ""
    estimated_duration_sec: float = 0.0
    notes: str = ""
    created_at: datetime = Field(default_factory=_utc_now)


class AnalyticsPack(BaseModel):
    report: AnalyticsReport = Field(default_factory=AnalyticsReport)
    notes: str = ""
    created_at: datetime = Field(default_factory=_utc_now)


class AnalyticsAgentResult(BaseModel):
    analytics: AnalyticsPack
    analytics_path: str
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "analytics": self.analytics.model_dump(mode="json"),
            "messages": list(self.messages),
        }
