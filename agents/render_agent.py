"""Render Agent — compose final MP4 + thumbnail (no Gemini)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from agents.base import BaseAgent
from core.errors import RenderAgentError, StorageError
from core.logging import get_logger
from core.paths import (
    ensure_project_analysis_dir,
    ensure_project_dir,
    ensure_project_renders_dir,
    get_render_plan_path,
)
from schemas.job import FeatureFlags, SourceType, VideoJobConfig
from schemas.project import ProjectMetadata
from schemas.render import RenderOp, RenderPack, RenderPlan, RenderResult
from tools.ffmpeg.audio_ops import normalize_loudness
from tools.ffmpeg.bin import resolve_ffmpeg_binary
from tools.ffmpeg.edit import concat_segments, cut_segment
from tools.ffmpeg.encode import encode_mp4
from tools.ffmpeg.probe import probe_media
from tools.ffmpeg.subs import burn_subtitles
from tools.ffmpeg.thumb import extract_thumbnail
from tools.ffmpeg.transform import resize

logger = get_logger(__name__)


def _aspect_dims(aspect: str, default_w: int = 1080, default_h: int = 1920) -> tuple[int, int]:
    mapping = {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350),
        "3:4": (1080, 1440),
    }
    key = (aspect or "").strip()
    if key in mapping:
        return mapping[key]
    try:
        a, b = key.split(":", 1)
        ratio = float(a) / float(b)
        if ratio < 1:
            return default_w, int(round(default_w / ratio))
        return int(round(default_h * ratio)), default_h
    except (ValueError, ZeroDivisionError):
        return default_w, default_h


class RenderAgent(BaseAgent):
    """Write render_plan.json first; compose renders/final.mp4 when possible."""

    name = "render"

    def run(
        self,
        project: ProjectMetadata | dict[str, Any],
        *,
        project_dir: str | Path | None = None,
        config: VideoJobConfig | dict[str, Any] | None = None,
        features: FeatureFlags | dict[str, Any] | None = None,
        clips: dict[str, Any] | None = None,
        captions_pack: dict[str, Any] | None = None,
        reframe_pack: dict[str, Any] | None = None,
        voice_pack: dict[str, Any] | None = None,
        music_pack: dict[str, Any] | None = None,
        platform_pack: dict[str, Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
        speech_transcript: dict[str, Any] | None = None,
        **_: Any,
    ) -> RenderResult:
        _ = features, voice_pack, music_pack  # notes-only reserved
        meta = self._coerce_project(project)
        project_id = meta.project_id
        root = Path(project_dir) if project_dir else ensure_project_dir(project_id)
        root.mkdir(parents=True, exist_ok=True)
        job_config = self._coerce_config(config)

        tw, th, aspect = self._resolve_target(reframe_pack, platform_pack, job_config)
        source = self._resolve_source(
            root, meta, reframe_pack, captions_pack, source_metadata, speech_transcript
        )
        burn, caption_path = self._caption_burn_info(captions_pack, platform_pack)

        ops: list[RenderOp] = []
        notes_parts: list[str] = []
        renders = root / "renders"
        renders.mkdir(parents=True, exist_ok=True)
        try:
            ensure_project_renders_dir(project_id)
        except Exception:  # noqa: BLE001
            pass

        out_video = renders / "final.mp4"
        out_thumb = renders / "thumbnail.jpg"
        source_type = getattr(meta, "source_type", None)
        is_script_only = source_type == SourceType.SCRIPT or str(source_type).lower() in {
            "script",
            "sourcetype.script",
        }

        plan = RenderPlan(
            project_id=project_id,
            source_path=str(source) if source else "",
            ops=ops,
            target_width=tw,
            target_height=th,
            target_aspect=aspect,
            burn_captions=burn,
            caption_path=caption_path,
            output_path=str(out_video),
            thumbnail_path=str(out_thumb),
            encoded=False,
            skipped=source is None,
            notes="Render plan created.",
        )
        pack = RenderPack(plan=plan, notes=plan.notes)
        path = self._write_pack(project_id, root, pack)
        messages = [
            f"[{self.name}] Plan written target={aspect} {tw}x{th}",
            f"[{self.name}] Wrote analysis/render_plan.json",
        ]

        if source is None:
            if not is_script_only:
                raise RenderAgentError(
                    "Render failed: no media source available for non-script job. "
                    "Expected source media before render stage."
                )
            plan.skipped = True
            plan.notes = "No media — plan only (soft-skip encode)."
            pack.notes = plan.notes
            path = self._write_pack(project_id, root, pack)
            messages.append(f"[{self.name}] Encode soft-skipped (no media).")
            return RenderResult(
                render_pack=pack, render_path=str(path), messages=messages
            )

        if resolve_ffmpeg_binary() is None:
            plan.skipped = True
            plan.notes = "FFmpeg unavailable — plan only (soft-skip encode)."
            pack.notes = plan.notes
            path = self._write_pack(project_id, root, pack)
            messages.append(f"[{self.name}] Encode soft-skipped (no FFmpeg).")
            return RenderResult(
                render_pack=pack, render_path=str(path), messages=messages
            )

        work = source
        try:
            work, clip_ops = self._apply_clips(work, clips, renders)
            ops.extend(clip_ops)

            if burn and caption_path and Path(caption_path).is_file():
                burned = renders / "_burned.mp4"
                result = burn_subtitles(work, caption_path, burned)
                if result is not None:
                    work = result
                    ops.append(RenderOp(name="burn_subtitles", detail=caption_path))
                else:
                    notes_parts.append("Caption burn soft-failed.")

            if tw > 0 and th > 0:
                resized = renders / "_resized.mp4"
                result = resize(work, resized, width=tw, height=th)
                if result is not None:
                    work = result
                    ops.append(RenderOp(name="resize", detail=f"{tw}x{th}"))
                else:
                    # Fallback encode with pad/scale
                    result = encode_mp4(work, resized, width=tw, height=th)
                    if result is not None:
                        work = result
                        ops.append(RenderOp(name="encode_resize", detail=f"{tw}x{th}"))

            normalized = renders / "_loudnorm.mp4"
            result = normalize_loudness(work, normalized)
            if result is not None:
                work = result
                ops.append(RenderOp(name="normalize_loudness", detail="loudnorm"))
            else:
                notes_parts.append("Loudnorm soft-skipped.")

            # Final copy/encode to final.mp4
            if work.resolve() != out_video.resolve():
                encoded = encode_mp4(work, out_video) or self._copy_media(
                    work, out_video
                )
            else:
                encoded = out_video if out_video.is_file() else None

            # Never claim success for unreadable / corrupt bytes (copy fallback trap)
            if encoded is not None and encoded.is_file() and not self._is_readable_media(
                encoded
            ):
                try:
                    if encoded.resolve() != Path(work).resolve():
                        encoded.unlink(missing_ok=True)
                except OSError:
                    pass
                encoded = None

            if encoded is not None and encoded.is_file():
                plan.encoded = True
                plan.skipped = False
                plan.output_path = str(encoded)
                ops.append(RenderOp(name="encode_mp4", detail=str(encoded)))
                messages.append(f"[{self.name}] Encoded {encoded}")
            else:
                plan.encoded = False
                plan.skipped = True
                plan.output_path = ""
                if out_video.is_file() and not self._is_readable_media(out_video):
                    try:
                        out_video.unlink(missing_ok=True)
                    except OSError:
                        pass
                notes_parts.append("Final encode soft-failed.")
                messages.append(f"[{self.name}] Encode soft-skipped.")

            if plan.encoded:
                thumb = extract_thumbnail(plan.output_path, out_thumb)
                if thumb is not None:
                    plan.thumbnail_path = str(thumb)
                    ops.append(RenderOp(name="extract_thumbnail", detail=str(thumb)))
                    messages.append(f"[{self.name}] Thumbnail {thumb}")
                else:
                    plan.thumbnail_path = ""
                    notes_parts.append("Thumbnail soft-failed.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Render compose error: %s", exc)
            plan.encoded = False
            notes_parts.append(f"Compose error: {exc}")
            messages.append(f"[{self.name}] Encode soft-skipped ({exc}).")

        # Honesty
        if plan.encoded and not (
            plan.output_path and Path(plan.output_path).is_file()
        ):
            plan.encoded = False
            plan.output_path = ""

        plan.ops = ops
        plan.notes = " ".join(notes_parts) if notes_parts else (
            "Rendered final.mp4" if plan.encoded else "Encode incomplete."
        )
        pack.plan = plan
        pack.notes = plan.notes
        path = self._write_pack(project_id, root, pack)
        logger.info(
            "RenderAgent ready project_id=%s encoded=%s",
            project_id,
            plan.encoded,
        )
        return RenderResult(
            render_pack=pack, render_path=str(path), messages=messages
        )

    def _resolve_target(
        self,
        reframe_pack: dict[str, Any] | None,
        platform_pack: dict[str, Any] | None,
        job_config: VideoJobConfig,
    ) -> tuple[int, int, str]:
        aspect = "9:16"
        tw, th = 1080, 1920
        if isinstance(reframe_pack, dict):
            plan = reframe_pack.get("plan") or {}
            if isinstance(plan, dict):
                if plan.get("target_aspect"):
                    aspect = str(plan["target_aspect"])
                try:
                    ow = int(plan.get("output_width") or 0)
                    oh = int(plan.get("output_height") or 0)
                    if ow > 0 and oh > 0:
                        tw, th = ow, oh
                except (TypeError, ValueError):
                    pass
        if isinstance(platform_pack, dict):
            pplan = platform_pack.get("plan") or {}
            meta = pplan.get("metadata") if isinstance(pplan, dict) else {}
            hints = pplan.get("export_hints") if isinstance(pplan, dict) else {}
            if isinstance(meta, dict) and meta.get("aspect_recommendation"):
                aspect = str(meta["aspect_recommendation"])
            if isinstance(hints, dict) and hints.get("preferred_aspect"):
                aspect = str(hints["preferred_aspect"])
        if getattr(job_config, "reframe_aspect", None):
            aspect = str(job_config.reframe_aspect) or aspect
        # If dims still default, derive from aspect
        if tw == 1080 and th == 1920:
            tw, th = _aspect_dims(aspect)
        return tw, th, aspect

    def _resolve_source(
        self,
        root: Path,
        meta: ProjectMetadata,
        reframe_pack: dict[str, Any] | None,
        captions_pack: dict[str, Any] | None,
        source_metadata: dict[str, Any] | None,
        speech_transcript: dict[str, Any] | None,
    ) -> Path | None:
        if isinstance(reframe_pack, dict):
            plan = reframe_pack.get("plan") or {}
            if isinstance(plan, dict) and plan.get("encoded") and plan.get("output_path"):
                p = Path(str(plan["output_path"]))
                if p.is_file():
                    return p
        if isinstance(captions_pack, dict):
            burned = str(captions_pack.get("burned_in_path") or "").strip()
            if burned and Path(burned).is_file():
                return Path(burned)
            plan = captions_pack.get("plan") or {}
            if isinstance(plan, dict) and plan.get("burn_in_applied"):
                cand = root / "captions" / "burned_in.mp4"
                if cand.is_file():
                    return cand

        for candidate in (
            root / "renders" / "reframed.mp4",
            root / "captions" / "burned_in.mp4",
        ):
            if candidate.is_file():
                return candidate

        if isinstance(speech_transcript, dict):
            mp = str(speech_transcript.get("media_path") or "").strip()
            if mp and Path(mp).is_file():
                return Path(mp)
        if isinstance(source_metadata, dict):
            for key in ("local_path", "media_path", "path", "file_path"):
                mp = str(source_metadata.get(key) or "").strip()
                if mp and Path(mp).is_file():
                    return Path(mp)
        sp = str(getattr(meta, "source_path", "") or "").strip()
        if sp and Path(sp).is_file():
            return Path(sp)
        return None

    def _caption_burn_info(
        self,
        captions_pack: dict[str, Any] | None,
        platform_pack: dict[str, Any] | None,
    ) -> tuple[bool, str]:
        burn = False
        caption_path = ""
        if isinstance(captions_pack, dict):
            plan = captions_pack.get("plan") or {}
            if isinstance(plan, dict):
                burn = bool(plan.get("burn_in_requested"))
            for key in ("ass_path", "srt_path", "vtt_path"):
                p = str(captions_pack.get(key) or "").strip()
                if p and Path(p).is_file():
                    caption_path = p
                    break
            # Already burned into source — skip re-burn
            if captions_pack.get("burned_in_path") and Path(
                str(captions_pack["burned_in_path"])
            ).is_file():
                if isinstance(plan, dict) and plan.get("burn_in_applied"):
                    burn = False
        if isinstance(platform_pack, dict):
            pplan = platform_pack.get("plan") or {}
            hints = pplan.get("export_hints") if isinstance(pplan, dict) else {}
            if isinstance(hints, dict) and hints.get("caption_burn_in") and caption_path:
                burn = True
        return burn, caption_path

    def _apply_clips(
        self,
        media: Path,
        clips: dict[str, Any] | None,
        renders: Path,
    ) -> tuple[Path, list[RenderOp]]:
        ops: list[RenderOp] = []
        if not isinstance(clips, dict):
            return media, ops
        items = clips.get("clips") or []
        if not isinstance(items, list) or not items:
            return media, ops
        segments: list[Path] = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            try:
                start = float(item.get("start") or 0.0)
                end = float(item.get("end") or 0.0)
            except (TypeError, ValueError):
                continue
            if end <= start:
                continue
            seg = renders / f"_clip_{i:03d}.mp4"
            cut = cut_segment(media, seg, start=start, end=end)
            if cut is not None:
                segments.append(cut)
                ops.append(
                    RenderOp(name="cut_segment", detail=f"{start:.2f}-{end:.2f}")
                )
        if not segments:
            return media, ops
        joined = renders / "_joined.mp4"
        result = concat_segments(segments, joined)
        if result is not None:
            ops.append(RenderOp(name="concat_segments", detail=str(len(segments))))
            return result, ops
        return media, ops

    def _is_readable_media(self, path: Path) -> bool:
        info = probe_media(path)
        if not info:
            return False
        try:
            duration = float(info.get("duration") or 0.0)
        except (TypeError, ValueError):
            duration = 0.0
        return bool(
            duration > 0.05
            or info.get("has_video")
            or info.get("has_audio")
            or int(info.get("width") or 0) > 0
        )

    def _copy_media(self, src: Path, dst: Path) -> Path | None:
        """Copy only when source is probeable media (never promote corrupt bytes)."""
        if not self._is_readable_media(src):
            return None
        try:
            shutil.copy2(src, dst)
            return dst if dst.is_file() and self._is_readable_media(dst) else None
        except OSError:
            return None

    def _coerce_project(
        self, project: ProjectMetadata | dict[str, Any]
    ) -> ProjectMetadata:
        if isinstance(project, ProjectMetadata):
            return project
        try:
            return ProjectMetadata.model_validate(project)
        except Exception as exc:  # noqa: BLE001
            raise RenderAgentError(f"Invalid project metadata: {exc}") from exc

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
            raise RenderAgentError(f"Invalid job config: {exc}") from exc

    def _write_pack(
        self, project_id: str, root: Path, pack: RenderPack
    ) -> Path:
        try:
            ensure_project_analysis_dir(project_id)
        except Exception:  # noqa: BLE001
            pass
        path = root / "analysis" / "render_plan.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(
                json.dumps(pack.model_dump(mode="json"), indent=2),
                encoding="utf-8",
            )
            # Also mirror via core path when possible
            try:
                alt = get_render_plan_path(project_id)
                if alt.resolve() != path.resolve():
                    alt.parent.mkdir(parents=True, exist_ok=True)
                    alt.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
        except OSError as exc:
            raise StorageError(f"Failed to write render plan: {exc}") from exc
        return path
