"""Supervisor Agent — intake validation and execution plan metadata."""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.errors import SupervisorAgentError
from core.logging import get_logger
from schemas.job import FeatureFlags, VideoJobConfig, VideoJobRequest
from schemas.supervisor import SupervisorAgentResult, SupervisorPlan

logger = get_logger(__name__)

DEFAULT_STAGES: list[str] = [
    "input",
    "ingest",
    "analysis",
    "research",
    "story",
    "script",
    "storyboard",
    "localization",
    "production",
    "platform",
    "render",
    "quality",
    "analytics",
    "export",
]


class SupervisorAgent(BaseAgent):
    """Validate the job request and record a lightweight execution plan."""

    name = "supervisor"

    def run(
        self,
        job: VideoJobRequest | dict[str, Any] | None = None,
        **_: Any,
    ) -> SupervisorAgentResult:
        try:
            request = self._coerce_job(job)
        except Exception as exc:  # noqa: BLE001
            raise SupervisorAgentError(f"Invalid job for supervisor: {exc}") from exc

        features = request.features or FeatureFlags()
        if not isinstance(features, FeatureFlags):
            features = FeatureFlags.model_validate(features)
        config = request.config or VideoJobConfig()
        if not isinstance(config, VideoJobConfig):
            config = VideoJobConfig.model_validate(config)

        feature_summary = {
            "enable_research": bool(features.enable_research),
            "smart_clip_detection": bool(features.smart_clip_detection),
            "viral_moments": bool(features.viral_moments),
            "funny_moments": bool(features.funny_moments),
            "platform_optimization": bool(features.platform_optimization),
            "captions": bool(features.captions),
        }
        source = (
            request.source_type.value
            if hasattr(request.source_type, "value")
            else str(request.source_type)
        )
        plan = SupervisorPlan(
            project_id=str(getattr(request, "job_id", "") or ""),
            source_type=source,
            next_agent="input",
            planned_stages=list(DEFAULT_STAGES),
            feature_summary=feature_summary,
            notes=(
                f"Supervisor accepted {source} job "
                f"(platform={config.platform}, type={config.video_type})."
            ),
        )
        messages = [
            f"[{self.name}] {plan.notes}",
            f"[{self.name}] Next agent → input",
        ]
        logger.info("SupervisorAgent ready source_type=%s", source)
        return SupervisorAgentResult(supervisor=plan, messages=messages)

    def _coerce_job(
        self, job: VideoJobRequest | dict[str, Any] | None
    ) -> VideoJobRequest:
        if job is None:
            raise SupervisorAgentError("Missing job payload")
        if isinstance(job, VideoJobRequest):
            return job
        return VideoJobRequest.model_validate(job)
