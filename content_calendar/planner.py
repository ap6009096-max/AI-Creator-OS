"""Smart Content Planner.

Generates 7-day, 30-day, and 90-day publishing strategy schedules.
"""

from __future__ import annotations

from typing import Any

from core.logging import get_logger
from schemas.calendar import (
    CalendarScheduledItem,
    ContentCalendarPack,
    ContentCalendarResult,
    ContentPlanPeriod,
)

logger = get_logger(__name__)


class SmartContentPlanner:
    """Generates structured content calendars based on creator niche and audience goals."""

    def generate_7_day(self, niche: str, goal: str) -> ContentPlanPeriod:
        items = [
            CalendarScheduledItem(
                day=1,
                date_label="Monday",
                content_title=f"The 5 Big Trends in {niche} for 2026",
                content_type="Long-form Video",
                platform="YouTube",
                target_time="10:00 AM EST",
                key_hook="Question: Have you noticed the sudden shift in...",
            ),
            CalendarScheduledItem(
                day=2,
                date_label="Tuesday",
                content_title=f"Top Mistake to Avoid in {niche}",
                content_type="Short Clip",
                platform="YouTube Shorts / Reels",
                target_time="02:00 PM EST",
                key_hook="Contrarian: Stop doing this immediately...",
            ),
            CalendarScheduledItem(
                day=3,
                date_label="Wednesday",
                content_title=f"Step-by-Step Framework for {niche}",
                content_type="LinkedIn Post",
                platform="LinkedIn",
                target_time="09:00 AM EST",
                key_hook="Story: How we scaled output by 3x...",
            ),
            CalendarScheduledItem(
                day=4,
                date_label="Thursday",
                content_title=f"5 Tools Every {niche} Creator Needs",
                content_type="X Thread",
                platform="X (Twitter)",
                target_time="11:30 AM EST",
                key_hook="Curiosity Gap: The secret tool top 1% use...",
            ),
            CalendarScheduledItem(
                day=5,
                date_label="Friday",
                content_title=f"Deep Dive Breakdown: {niche} Blueprint",
                content_type="Blog Article",
                platform="Medium / Substack",
                target_time="08:00 AM EST",
                key_hook="Authority: The definitive 2026 guide...",
            ),
            CalendarScheduledItem(
                day=6,
                date_label="Saturday",
                content_title=f"Behind the Scenes: How We Produce Content",
                content_type="Reel / TikTok",
                platform="Instagram / TikTok",
                target_time="05:00 PM EST",
                key_hook="Behind-the-scenes visual hook...",
            ),
            CalendarScheduledItem(
                day=7,
                date_label="Sunday",
                content_title=f"Weekly Q&A & Community Recap",
                content_type="Community Post / Reel",
                platform="YouTube / IG Stories",
                target_time="06:00 PM EST",
                key_hook="Community engagement question...",
            ),
        ]
        return ContentPlanPeriod(timeframe="7-day", niche=niche, goal=goal, items=items)

    def generate_30_day(self, niche: str, goal: str) -> ContentPlanPeriod:
        items = []
        for week in range(1, 5):
            items.append(
                CalendarScheduledItem(
                    day=(week - 1) * 7 + 1,
                    date_label=f"Week {week} - Launch",
                    content_title=f"Pillar Topic #{week}: Scaling {niche}",
                    content_type="Long-form Video",
                    platform="YouTube",
                    target_time="10:00 AM EST",
                    key_hook=f"Week {week} Masterclass Hook",
                )
            )
            items.append(
                CalendarScheduledItem(
                    day=(week - 1) * 7 + 3,
                    date_label=f"Week {week} - Breakdown",
                    content_title=f"Micro-Lesson #{week} for {niche}",
                    content_type="Short Clip",
                    platform="Reels / Shorts",
                    target_time="02:00 PM EST",
                    key_hook=f"High-impact Short Hook",
                )
            )
        return ContentPlanPeriod(timeframe="30-day", niche=niche, goal=goal, items=items)

    def generate_90_day(self, niche: str, goal: str) -> ContentPlanPeriod:
        items = []
        for month in range(1, 4):
            items.append(
                CalendarScheduledItem(
                    day=(month - 1) * 30 + 1,
                    date_label=f"Month {month} Theme",
                    content_title=f"Quarterly Milestone Strategy #{month}: Dominating {niche}",
                    content_type="Multi-Part Series",
                    platform="All Platforms",
                    target_time="10:00 AM EST",
                    key_hook=f"Quarterly Authority Campaign Hook",
                )
            )
        return ContentPlanPeriod(timeframe="90-day", niche=niche, goal=goal, items=items)

    def plan(self, niche: str = "Tech & AI", goal: str = "Audience Growth") -> ContentCalendarPack:
        return ContentCalendarPack(
            plan_7_day=self.generate_7_day(niche, goal),
            plan_30_day=self.generate_30_day(niche, goal),
            plan_90_day=self.generate_90_day(niche, goal),
        )

    def run(self, niche: str = "Tech & AI", goal: str = "Audience Growth") -> ContentCalendarResult:
        pack = self.plan(niche, goal)
        messages = [
            f"[smart_content_calendar] Generated 7-day ({len(pack.plan_7_day.items)} items), 30-day ({len(pack.plan_30_day.items)} items), and 90-day content calendar for niche '{niche}'."
        ]
        return ContentCalendarResult(calendar_plan=pack, messages=messages)
