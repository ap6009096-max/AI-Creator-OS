"""AI Quality Assurance Agent schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class QAScoreBreakdown(BaseModel):
    grammar_score: float = 20.0  # 0 - 20
    fact_consistency_score: float = 20.0  # 0 - 20
    seo_score: float = 18.0  # 0 - 20
    copyright_risk_score: float = 20.0  # 0 - 20 (20 = safe, 0 = high risk)
    readability_score: float = 17.0  # 0 - 20


class QAFlaggedIssue(BaseModel):
    category: str
    issue: str
    suggestion: str
    severity: str = "warning"  # info, warning, critical


class AIQAReport(BaseModel):
    overall_score: float = 95.0
    passed: bool = True
    threshold: float = 85.0
    breakdown: QAScoreBreakdown = Field(default_factory=QAScoreBreakdown)
    flagged_issues: list[QAFlaggedIssue] = Field(default_factory=list)
    summary_verdict: str = "Passed AI Quality & Compliance Review."


class AIQAResult(BaseModel):
    qa_report: AIQAReport
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "qa_report": self.qa_report.model_dump(mode="json"),
            "messages": list(self.messages),
        }
