"""Creator Dashboard Analytics schemas."""

from __future__ import annotations

from pydantic import BaseModel


class CreatorDashboardMetrics(BaseModel):
    total_projects: int = 0
    total_videos_generated: int = 0
    total_shorts_generated: int = 0
    total_posts_generated: int = 0
    hours_saved: float = 0.0  # Projects * 8.5
    cost_saved_usd: float = 0.0  # Videos * 350 + Shorts * 75
    efficiency_multiplier: float = 12.5  # 12.5x faster than manual production
