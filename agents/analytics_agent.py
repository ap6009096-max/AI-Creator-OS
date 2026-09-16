"""Analytics Agent — rollup metrics after quality, before export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.base import BaseAgent
from core.errors import AnalyticsAgentError, StorageError
from core.logging import get_logger
from core.paths import ensure_project_analysis_dir, ensure_project_dir
from schemas.analytics import AnalyticsAgentResult, AnalyticsPack, AnalyticsReport
from schemas.job import VideoJobConfig
from schemas.project import ProjectMetadata

logger = get_logger(__name__)


class AnalyticsAgent(BaseAgent):
    """Aggregate pipeline counters into analysis/analytics.json."""

    name = "analytics"

    def run(
        self,
        project: ProjectMetadata | dict[str, Any],
        *,
        project_dir: str | Path | None = None,
        config: VideoJobConfig | dict[str, Any] | None = None,
        clips: dict[str, Any] | None = None,
        stories: dict[str, Any] | None = None,
        scripts: dict[str, Any] | None = None,
        storyboard: dict[str, Any] | None = None,
        research: dict[str, Any] | None = None,
        quality_pack: dict[str, Any] | None = None,
        render_pack: dict[str, Any] | None = None,
        platform_pack: dict[str, Any] | None = None,
        locale_pack: dict[str, Any] | None = None,
        country_profile: dict[str, Any] | None = None,
        **_: Any,
    ) -> AnalyticsAgentResult:
        meta = self._coerce_project(project)
        project_id = meta.project_id
        root = Path(project_dir) if project_dir else ensure_project_dir(project_id)
        root.mkdir(parents=True, exist_ok=True)
        job_config = self._coerce_config(config)

        clip_list = (clips or {}).get("clips") or []
        story_list = (stories or {}).get("stories") or []
        script_list = (scripts or {}).get("scripts") or []
        frames = (storyboard or {}).get("frames") or []
        research_results = (research or {}).get("results") or []

        quality_passed: bool | None = None
        quality_skipped = False
        if isinstance(quality_pack, dict):
            report = quality_pack.get("report") or {}
            if isinstance(report, dict):
                if "passed" in report:
                    quality_passed = bool(report.get("passed"))
                quality_skipped = bool(report.get("skipped"))

        render_skipped = False
        if isinstance(render_pack, dict):
            plan = render_pack.get("plan") or {}
            if isinstance(plan, dict):
                render_skipped = bool(plan.get("skipped")) and not bool(
                    plan.get("encoded")
                )

        platform = job_config.platform
        if isinstance(platform_pack, dict):
            preset = platform_pack.get("preset") or {}
            if isinstance(preset, dict) and preset.get("name"):
                platform = str(preset["name"])

        language = job_config.language
        country = job_config.country
        if isinstance(locale_pack, dict):
            language = str(locale_pack.get("language") or language)
        if isinstance(country_profile, dict):
            country = str(
                country_profile.get("country")
                or country_profile.get("name")
                or country
            )

        duration = 0.0
        for clip in clip_list:
            if isinstance(clip, dict):
                try:
                    duration += float(clip.get("duration") or 0.0)
                except (TypeError, ValueError):
                    pass
        if duration <= 0 and frames:
            for frame in frames:
                if isinstance(frame, dict):
                    try:
                        duration += float(frame.get("duration_hint_sec") or 0.0)
                    except (TypeError, ValueError):
                        pass

        report = AnalyticsReport(
            project_id=project_id,
            clip_count=len(clip_list) if isinstance(clip_list, list) else 0,
            story_count=len(story_list) if isinstance(story_list, list) else 0,
            script_count=len(script_list) if isinstance(script_list, list) else 0,
            storyboard_frame_count=len(frames) if isinstance(frames, list) else 0,
            research_result_count=(
                len(research_results) if isinstance(research_results, list) else 0
            ),
            quality_passed=quality_passed,
            quality_skipped=quality_skipped,
            render_skipped=render_skipped,
            platform=platform,
            localization_language=language,
            localization_country=country,
            estimated_duration_sec=round(duration, 2),
            notes="Analytics rollup complete.",
        )
        pack = AnalyticsPack(report=report, notes=report.notes)
        path = self._write_pack(project_id, root, pack)
        messages = [
            f"[{self.name}] clips={report.clip_count} "
            f"quality_passed={report.quality_passed} "
            f"duration≈{report.estimated_duration_sec}s",
            f"[{self.name}] Wrote analysis/analytics.json",
        ]
        logger.info(
            "AnalyticsAgent ready project_id=%s clips=%s",
            project_id,
            report.clip_count,
        )
        return AnalyticsAgentResult(
            analytics=pack, analytics_path=str(path), messages=messages
        )

    def _coerce_project(
        self, project: ProjectMetadata | dict[str, Any]
    ) -> ProjectMetadata:
        if isinstance(project, ProjectMetadata):
            return project
        try:
            return ProjectMetadata.model_validate(project)
        except Exception as exc:  # noqa: BLE001
            raise AnalyticsAgentError(f"Invalid project metadata: {exc}") from exc

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
            raise AnalyticsAgentError(f"Invalid job config: {exc}") from exc

    def _write_pack(self, project_id: str, root: Path, pack: AnalyticsPack) -> Path:
        path = root / "analysis" / "analytics.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                ensure_project_analysis_dir(project_id)
            except Exception:  # noqa: BLE001
                pass
            path.write_text(
                json.dumps(pack.model_dump(mode="json"), indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError(f"Failed to write analytics.json: {exc}") from exc
        return path
