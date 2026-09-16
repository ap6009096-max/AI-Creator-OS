"""Supervisor agent schemas (intake / execution plan metadata)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SupervisorPlan(BaseModel):
    project_id: str = ""
    source_type: str = ""
    next_agent: str = "input"
    planned_stages: list[str] = Field(default_factory=list)
    feature_summary: dict[str, bool] = Field(default_factory=dict)
    notes: str = ""
    created_at: datetime = Field(default_factory=_utc_now)


class SupervisorAgentResult(BaseModel):
    supervisor: SupervisorPlan
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "supervisor": self.supervisor.model_dump(mode="json"),
            "next_agent": self.supervisor.next_agent,
            "messages": list(self.messages),
        }
