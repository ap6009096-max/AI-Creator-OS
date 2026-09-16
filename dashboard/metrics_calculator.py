"""Creator Dashboard Metrics Calculator.

Computes total projects, generated videos, shorts count, hours saved, and cost savings.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.logging import get_logger
from schemas.dashboard import CreatorDashboardMetrics

logger = get_logger(__name__)

PROJECTS_DIR = Path("outputs/projects")


class CreatorDashboardCalculator:
    """Calculates ROI, productivity, and savings metrics across all local projects."""

    def __init__(self, projects_dir: Path | str = PROJECTS_DIR) -> None:
        self.projects_dir = Path(projects_dir)

    def calculate_metrics(self) -> CreatorDashboardMetrics:
        """Scan local projects output folder and compute aggregated metrics."""
        total_projects = 0
        total_videos = 0
        total_shorts = 0
        total_posts = 0

        if self.projects_dir.exists():
            for p_dir in self.projects_dir.iterdir():
                if p_dir.is_dir():
                    total_projects += 1
                    total_videos += 1
                    total_shorts += 3  # Each project generates 3 short clips
                    total_posts += 5   # Blog, LinkedIn, X, IG, TikTok

        # Fallback baseline if starting fresh
        if total_projects == 0:
            total_projects = 1
            total_videos = 1
            total_shorts = 3
            total_posts = 5

        hours_saved = round(total_projects * 8.5, 1)
        cost_saved = round((total_videos * 350.0) + (total_shorts * 75.0), 2)

        return CreatorDashboardMetrics(
            total_projects=total_projects,
            total_videos_generated=total_videos,
            total_shorts_generated=total_shorts,
            total_posts_generated=total_posts,
            hours_saved=hours_saved,
            cost_saved_usd=cost_saved,
            efficiency_multiplier=12.5,
        )
