"""Research Agent — Parallel Search grounding for content planning."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from agents.base import BaseAgent
from config.settings import get_settings
from core.errors import ResearchAgentError, StorageError
from core.logging import get_logger
from core.paths import ensure_project_analysis_dir, ensure_project_dir
from schemas.job import FeatureFlags, VideoJobConfig
from schemas.project import ProjectMetadata
from schemas.research import (
    GeminiResearchPlan,
    ResearchAgentResult,
    ResearchHit,
    ResearchReport,
)
from tools.research.parallel_search import run_parallel_search

logger = get_logger(__name__)

GeneratePlanFn = Callable[..., GeminiResearchPlan]
SearchFn = Callable[..., Any]


def _heuristic_plan(topic_hint: str, video_type: str) -> GeminiResearchPlan:
    words = re.findall(r"[A-Za-z0-9]{3,}", topic_hint or "")
    seed = " ".join(words[:6]) or video_type or "short form video"
    return GeminiResearchPlan(
        objective=f"Find current context and trends for: {seed}",
        search_queries=[
            f"{seed} trends",
            f"{seed} tips",
            f"{video_type} best practices",
        ],
    )


class ResearchAgent(BaseAgent):
    """Plan search queries (Gemini or heuristic) and call Parallel Search."""

    name = "research"

    def __init__(
        self,
        *,
        plan_fn: GeneratePlanFn | None = None,
        search_fn: SearchFn | None = None,
    ) -> None:
        self._plan_fn = plan_fn
        self._search_fn = search_fn

    def run(
        self,
        project: ProjectMetadata | dict[str, Any],
        *,
        project_dir: str | Path | None = None,
        config: VideoJobConfig | dict[str, Any] | None = None,
        features: FeatureFlags | dict[str, Any] | None = None,
        clips: dict[str, Any] | None = None,
        transcript: dict[str, Any] | None = None,
        speech_transcript: dict[str, Any] | None = None,
        force_skip: bool = False,
        **_: Any,
    ) -> ResearchAgentResult:
        meta = self._coerce_project(project)
        project_id = meta.project_id
        root = Path(project_dir) if project_dir else ensure_project_dir(project_id)
        root.mkdir(parents=True, exist_ok=True)
        job_config = self._coerce_config(config)
        flags = self._coerce_features(features)
        settings = get_settings()

        if force_skip or not flags.enable_research:
            report = ResearchReport(
                project_id=project_id,
                skipped=True,
                notes="Research skipped (feature off).",
            )
            path = self._write_report(project_id, root, report)
            return ResearchAgentResult(
                research=report,
                research_path=str(path),
                messages=[f"[{self.name}] Skipped (feature off)"],
            )

        if not settings.has_parallel_api_key and self._search_fn is None:
            report = ResearchReport(
                project_id=project_id,
                skipped=True,
                notes="Research skipped (PARALLEL_API_KEY not configured).",
            )
            path = self._write_report(project_id, root, report)
            return ResearchAgentResult(
                research=report,
                research_path=str(path),
                messages=[f"[{self.name}] Skipped (no PARALLEL_API_KEY)"],
            )

        topic_hint = self._topic_hint(meta, transcript, speech_transcript, clips)
        clip_summaries = self._clip_summaries(clips)

        try:
            plan_fn = self._plan_fn
            if plan_fn is None:
                from tools.llm.gemini import generate_research_plan

                plan_fn = generate_research_plan
            try:
                plan = plan_fn(
                    topic_hint=topic_hint,
                    video_type=job_config.video_type,
                    platform=job_config.platform,
                    audience=job_config.audience,
                    clip_summaries=clip_summaries,
                )
            except Exception:  # noqa: BLE001
                logger.warning("Research plan Gemini failed; using heuristic queries")
                plan = _heuristic_plan(topic_hint, job_config.video_type)

            if not isinstance(plan, GeminiResearchPlan):
                plan = GeminiResearchPlan.model_validate(plan)
            if len(plan.search_queries) < 3:
                fallback = _heuristic_plan(topic_hint, job_config.video_type)
                merged = list(plan.search_queries) + list(fallback.search_queries)
                plan.search_queries = merged[:3]
                if not plan.objective:
                    plan.objective = fallback.objective

            search = self._search_fn or run_parallel_search
            search_result = search(
                objective=plan.objective,
                search_queries=plan.search_queries,
            )
            hits_raw = getattr(search_result, "results", None)
            if hits_raw is None and isinstance(search_result, dict):
                hits_raw = search_result.get("results") or []
            hits = [
                ResearchHit.model_validate(h) if not isinstance(h, ResearchHit) else h
                for h in (hits_raw or [])
            ]
            report = ResearchReport(
                project_id=project_id,
                objective=getattr(search_result, "objective", None) or plan.objective,
                search_queries=list(
                    getattr(search_result, "search_queries", None) or plan.search_queries
                ),
                results=hits,
                skipped=False,
                notes=f"Parallel Search returned {len(hits)} result(s).",
            )
        except ResearchAgentError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ResearchAgentError(f"Research agent failed: {exc}") from exc

        path = self._write_report(project_id, root, report)
        messages = [
            f"[{self.name}] {report.notes}",
            f"[{self.name}] Wrote analysis/research.json",
        ]
        logger.info(
            "ResearchAgent ready project_id=%s hits=%s skipped=%s",
            project_id,
            len(report.results),
            report.skipped,
        )
        return ResearchAgentResult(
            research=report, research_path=str(path), messages=messages
        )

    def _topic_hint(
        self,
        meta: ProjectMetadata,
        transcript: dict[str, Any] | None,
        speech_transcript: dict[str, Any] | None,
        clips: dict[str, Any] | None,
    ) -> str:
        parts: list[str] = []
        raw = getattr(meta, "raw_text", None) or ""
        if raw:
            parts.append(str(raw)[:800])
        title = getattr(meta, "title", None) or ""
        if title:
            parts.append(str(title))
        if speech_transcript and speech_transcript.get("text"):
            parts.append(str(speech_transcript["text"])[:800])
        elif transcript and transcript.get("text"):
            parts.append(str(transcript["text"])[:800])
        elif transcript and transcript.get("cleaned_text"):
            parts.append(str(transcript["cleaned_text"])[:800])
        if clips:
            for clip in (clips.get("clips") or [])[:3]:
                if isinstance(clip, dict) and clip.get("transcript"):
                    parts.append(str(clip["transcript"])[:200])
        return "\n".join(parts) or "short form video content"

    def _clip_summaries(self, clips: dict[str, Any] | None) -> list[str]:
        out: list[str] = []
        if not clips:
            return out
        for clip in clips.get("clips") or []:
            if not isinstance(clip, dict):
                continue
            title = str(clip.get("title") or clip.get("hook") or "").strip()
            cat = str(clip.get("category") or "").strip()
            excerpt = str(clip.get("transcript") or "")[:120].strip()
            out.append(f"#{clip.get('id', '?')} {title or cat}: {excerpt}".strip(": "))
        return out

    def _coerce_project(
        self, project: ProjectMetadata | dict[str, Any]
    ) -> ProjectMetadata:
        if isinstance(project, ProjectMetadata):
            return project
        try:
            return ProjectMetadata.model_validate(project)
        except Exception as exc:  # noqa: BLE001
            raise ResearchAgentError(f"Invalid project metadata: {exc}") from exc

    def _coerce_config(
        self, config: VideoJobConfig | dict[str, Any] | None
    ) -> VideoJobConfig:
        if config is None:
            return VideoJobConfig()
        if isinstance(config, VideoJobConfig):
            return config
        try:
            return VideoJobConfig.model_validate(config)
        except Exception as exc:  # noqa: BLE001
            raise ResearchAgentError(f"Invalid job config: {exc}") from exc

    def _coerce_features(
        self, features: FeatureFlags | dict[str, Any] | None
    ) -> FeatureFlags:
        if features is None:
            return FeatureFlags()
        if isinstance(features, FeatureFlags):
            return features
        try:
            return FeatureFlags.model_validate(features)
        except Exception as exc:  # noqa: BLE001
            raise ResearchAgentError(f"Invalid feature flags: {exc}") from exc

    def _write_report(
        self, project_id: str, root: Path, report: ResearchReport
    ) -> Path:
        path = root / "analysis" / "research.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                ensure_project_analysis_dir(project_id)
            except Exception:  # noqa: BLE001
                pass
            path.write_text(
                json.dumps(report.model_dump(mode="json"), indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError(f"Failed to write research.json: {exc}") from exc
        return path
