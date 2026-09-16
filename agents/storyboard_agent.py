"""Storyboard Agent — ordered shot frames from scripts/stories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from agents.base import BaseAgent
from core.errors import StorageError, StoryboardAgentError
from core.logging import get_logger
from core.paths import ensure_project_analysis_dir, ensure_project_dir
from schemas.job import VideoJobConfig
from schemas.project import ProjectMetadata
from schemas.storyboard import (
    GeminiStoryboardBatch,
    GeminiStoryboardFrame,
    StoryboardAgentResult,
    StoryboardFrame,
    StoryboardReport,
)

logger = get_logger(__name__)

GenerateStoryboardFn = Callable[..., GeminiStoryboardBatch]


class StoryboardAgent(BaseAgent):
    """Generate storyboard frames via Gemini (injectable for tests)."""

    name = "storyboard"

    def __init__(self, generate_fn: GenerateStoryboardFn | None = None) -> None:
        self._generate_fn = generate_fn

    def run(
        self,
        project: ProjectMetadata | dict[str, Any],
        *,
        project_dir: str | Path | None = None,
        config: VideoJobConfig | dict[str, Any] | None = None,
        scripts: dict[str, Any] | None = None,
        stories: dict[str, Any] | None = None,
        clips: dict[str, Any] | None = None,
        **_: Any,
    ) -> StoryboardAgentResult:
        meta = self._coerce_project(project)
        project_id = meta.project_id
        root = Path(project_dir) if project_dir else ensure_project_dir(project_id)
        root.mkdir(parents=True, exist_ok=True)
        job_config = self._coerce_config(config)

        script_list = (scripts or {}).get("scripts") or []
        story_list = (stories or {}).get("stories") or []
        if not script_list and not story_list:
            report = StoryboardReport(
                project_id=project_id,
                skipped=True,
                notes="Storyboard skipped (no scripts or stories).",
            )
            path = self._write_report(project_id, root, report)
            return StoryboardAgentResult(
                storyboard=report,
                storyboard_path=str(path),
                messages=[f"[{self.name}] Skipped (no scripts/stories)"],
            )

        script_blocks = self._script_blocks(script_list)
        story_blocks = self._story_blocks(story_list)

        try:
            generate = self._generate_fn
            if generate is None:
                from tools.llm.gemini import generate_storyboard

                generate = generate_storyboard
            batch = generate(
                script_blocks=script_blocks,
                story_blocks=story_blocks,
                video_type=job_config.video_type,
            )
            if not isinstance(batch, GeminiStoryboardBatch):
                batch = GeminiStoryboardBatch.model_validate(batch)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Storyboard Gemini failed; building heuristic frames: %s", exc)
            batch = self._heuristic_batch(script_list, story_list)

        frames = [
            StoryboardFrame(
                frame_index=int(f.frame_index if f.frame_index else i),
                clip_id=int(f.clip_id),
                shot_intent=f.shot_intent or "Establish beat",
                on_screen_text=f.on_screen_text or "",
                narration=f.narration or "",
                duration_hint_sec=float(f.duration_hint_sec or 3.0),
                visual_notes=f.visual_notes or "",
            )
            for i, f in enumerate(batch.frames)
        ]
        if not frames:
            frames = [
                StoryboardFrame.model_validate(f.model_dump())
                for f in self._heuristic_batch(script_list, story_list).frames
            ]

        # Optional duration hints from clips
        clip_by_id = {
            int(c.get("id", i)): c
            for i, c in enumerate((clips or {}).get("clips") or [])
            if isinstance(c, dict)
        }
        for frame in frames:
            clip = clip_by_id.get(frame.clip_id)
            if clip and not frame.duration_hint_sec:
                try:
                    frame.duration_hint_sec = float(clip.get("duration") or 3.0)
                except (TypeError, ValueError):
                    pass

        report = StoryboardReport(
            project_id=project_id,
            frames=frames,
            skipped=False,
            notes=f"Storyboard ready with {len(frames)} frame(s).",
        )
        path = self._write_report(project_id, root, report)
        messages = [
            f"[{self.name}] {report.notes}",
            f"[{self.name}] Wrote analysis/storyboard.json",
        ]
        logger.info(
            "StoryboardAgent ready project_id=%s frames=%s",
            project_id,
            len(frames),
        )
        return StoryboardAgentResult(
            storyboard=report, storyboard_path=str(path), messages=messages
        )

    def _script_blocks(self, scripts: list[Any]) -> list[str]:
        blocks: list[str] = []
        for s in scripts:
            if not isinstance(s, dict):
                continue
            blocks.append(
                f"clip_id={s.get('clip_id', 0)}\n"
                f"title={s.get('title', '')}\n"
                f"hook={s.get('hook', '')}\n"
                f"script={s.get('short_script', '')}\n"
                f"cta={s.get('cta', '')}"
            )
        return blocks

    def _story_blocks(self, stories: list[Any]) -> list[str]:
        blocks: list[str] = []
        for s in stories:
            if not isinstance(s, dict):
                continue
            structure = s.get("structure") or {}
            blocks.append(
                f"clip_id={s.get('clip_id', 0)}\n"
                f"hook={structure.get('hook', '')}\n"
                f"context={structure.get('context', '')}\n"
                f"value_event={structure.get('value_event', '')}\n"
                f"payoff={structure.get('payoff', '')}\n"
                f"cta={structure.get('cta', '')}"
            )
        return blocks

    def _heuristic_batch(
        self, scripts: list[Any], stories: list[Any]
    ) -> GeminiStoryboardBatch:
        frames: list[GeminiStoryboardFrame] = []
        source = scripts or stories
        for i, item in enumerate(source):
            if not isinstance(item, dict):
                continue
            clip_id = int(item.get("clip_id", i))
            if scripts:
                frames.append(
                    GeminiStoryboardFrame(
                        frame_index=i,
                        clip_id=clip_id,
                        shot_intent="Open on hook",
                        on_screen_text=str(item.get("thumbnail_text") or item.get("title") or "")[
                            :80
                        ],
                        narration=str(item.get("short_script") or item.get("hook") or "")[:240],
                        duration_hint_sec=4.0,
                        visual_notes="Match energy to hook; keep subject centered.",
                    )
                )
            else:
                structure = item.get("structure") or {}
                frames.append(
                    GeminiStoryboardFrame(
                        frame_index=i,
                        clip_id=clip_id,
                        shot_intent="Story beat",
                        on_screen_text=str(structure.get("hook") or "")[:80],
                        narration=str(structure.get("value_event") or "")[:240],
                        duration_hint_sec=4.0,
                        visual_notes="Visualize payoff clearly.",
                    )
                )
        return GeminiStoryboardBatch(frames=frames)

    def _coerce_project(
        self, project: ProjectMetadata | dict[str, Any]
    ) -> ProjectMetadata:
        if isinstance(project, ProjectMetadata):
            return project
        try:
            return ProjectMetadata.model_validate(project)
        except Exception as exc:  # noqa: BLE001
            raise StoryboardAgentError(f"Invalid project metadata: {exc}") from exc

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
            raise StoryboardAgentError(f"Invalid job config: {exc}") from exc

    def _write_report(
        self, project_id: str, root: Path, report: StoryboardReport
    ) -> Path:
        path = root / "analysis" / "storyboard.json"
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
            raise StorageError(f"Failed to write storyboard.json: {exc}") from exc
        return path
