"""Viral Content Intelligence schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ViralHookOption(BaseModel):
    hook_type: str  # Question, Contrarian, Curiosity Gap, Story, Statistics
    hook_text: str
    predicted_impact: float = 85.0  # 0 to 100
    rationale: str = ""


class ViralContentIntelligencePack(BaseModel):
    topic: str = ""
    predicted_engagement_score: float = 88.0
    predicted_retention_score: float = 82.0
    viral_hooks: list[ViralHookOption] = Field(default_factory=list)
    key_retention_triggers: list[str] = Field(default_factory=list)
    pre_generation_recommendations: list[str] = Field(default_factory=list)
    trend_sentiment: str = "High Growth Interest"


class ViralIntelligenceResult(BaseModel):
    viral_analysis: ViralContentIntelligencePack
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "viral_analysis": self.viral_analysis.model_dump(mode="json"),
            "messages": list(self.messages),
        }
