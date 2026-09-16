"""Smart Content Calendar schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class CalendarScheduledItem(BaseModel):
    day: int
    date_label: str
    content_title: str
    content_type: str  # Long-form, Short, LinkedIn, X Thread, Blog
    platform: str
    target_time: str
    status: str = "Scheduled"
    key_hook: str = ""


class ContentPlanPeriod(BaseModel):
    timeframe: str  # 7-day, 30-day, 90-day
    niche: str = ""
    goal: str = ""
    items: list[CalendarScheduledItem] = Field(default_factory=list)


class ContentCalendarPack(BaseModel):
    plan_7_day: ContentPlanPeriod = Field(default_factory=lambda: ContentPlanPeriod(timeframe="7-day"))
    plan_30_day: ContentPlanPeriod = Field(default_factory=lambda: ContentPlanPeriod(timeframe="30-day"))
    plan_90_day: ContentPlanPeriod = Field(default_factory=lambda: ContentPlanPeriod(timeframe="90-day"))


class ContentCalendarResult(BaseModel):
    calendar_plan: ContentCalendarPack
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "calendar_plan": self.calendar_plan.model_dump(mode="json"),
            "messages": list(self.messages),
        }
