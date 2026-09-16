"""Research agent schemas (Parallel Search grounding)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchHit(BaseModel):
    title: str = ""
    url: str = ""
    excerpts: list[str] = Field(default_factory=list)


class GeminiResearchPlan(BaseModel):
    """Lean Gemini output: search objective + keyword queries."""

    objective: str = ""
    search_queries: list[str] = Field(default_factory=list)


class ResearchReport(BaseModel):
    project_id: str = ""
    objective: str = ""
    search_queries: list[str] = Field(default_factory=list)
    results: list[ResearchHit] = Field(default_factory=list)
    provider: str = "parallel-search"
    skipped: bool = False
    notes: str = ""
    created_at: datetime = Field(default_factory=_utc_now)


class ResearchAgentResult(BaseModel):
    research: ResearchReport
    research_path: str
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "research": self.research.model_dump(mode="json"),
            "messages": list(self.messages),
        }
