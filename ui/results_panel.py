"""Results panel — clips, localization, captions, platform, video, quality."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def render_results_panel(result: dict[str, Any] | None = None) -> None:
    """Render end-of-job deliverables from workflow result / session."""
    data = result or st.session_state.get("last_result")
    if not isinstance(data, dict) or not data:
        return

    st.subheader("Results")
    project_dir = data.get("project_dir") or ""
    if project_dir:
        st.caption(f"Project folder: `{project_dir}`")

    tabs = st.tabs(
        [
            "Clips",
            "Localization",
            "Captions",
            "Platform",
            "Video",
            "Quality",
            "Files",
        ]
    )

    with tabs[0]:
        clips = _as_dict(data.get("selected_clips") or data.get("clips"))
        items = clips.get("clips") if isinstance(clips.get("clips"), list) else []
        if not items and isinstance(clips.get("report"), dict):
            items = clips["report"].get("clips") or []
        if items:
            for i, clip in enumerate(items[:30]):
                if not isinstance(clip, dict):
                    continue
                st.markdown(
                    f"**Clip {clip.get('id', i)}** · "
                    f"{clip.get('start', '?')}s → {clip.get('end', '?')}s · "
                    f"score={clip.get('score', clip.get('final_score', ''))}"
                )
                if clip.get("title") or clip.get("reason"):
                    st.caption(str(clip.get("title") or clip.get("reason") or ""))
        else:
            st.info("No clips selected for this job.")

    with tabs[1]:
        locs = data.get("localizations") or data.get("cultural_context")
        if isinstance(locs, dict):
            st.json(locs)
        else:
            st.info("No localization pack available.")
        humor = data.get("humor_context") or data.get("humor_localization")
        if humor:
            with st.expander("Humor context"):
                st.json(humor)

    with tabs[2]:
        captions = _as_dict(data.get("captions") or data.get("captions_pack"))
        for key, label in (
            ("srt_path", "SRT"),
            ("vtt_path", "VTT"),
            ("ass_path", "ASS"),
        ):
            path = str(captions.get(key) or "").strip()
            if path and Path(path).is_file():
                st.markdown(f"**{label}:** `{path}`")
                try:
                    preview = Path(path).read_text(encoding="utf-8", errors="ignore")
                    st.code(preview[:2000], language="text")
                except OSError:
                    pass
            elif path:
                st.markdown(f"**{label}:** `{path}` (missing on disk)")
        if project_dir:
            sub = Path(project_dir) / "subtitles"
            if sub.is_dir():
                files = list(sub.glob("*"))
                if files:
                    st.markdown("**subtitles/**")
                    for f in files:
                        st.write(f"- `{f}`")

    with tabs[3]:
        meta = data.get("platform_metadata")
        if not meta:
            pack = _as_dict(data.get("platform_pack") or data.get("platform"))
            plan = _as_dict(pack.get("plan"))
            meta = plan.get("metadata") or pack
        if meta:
            st.json(meta)
        else:
            st.info("No platform metadata.")
        if project_dir:
            p = Path(project_dir) / "exports" / "platform_metadata.json"
            if p.is_file():
                st.caption(f"Also on disk: `{p}`")

    with tabs[4]:
        video_path = str(data.get("video_path") or "").strip()
        export_pack = _as_dict(data.get("export_pack"))
        export_bundle = _as_dict(export_pack.get("bundle"))
        if not video_path:
            video_path = str(export_bundle.get("video_path") or "").strip()
        if not video_path:
            export_path = str(export_pack.get("export_path") or "").strip()
            if export_path.lower().endswith(".mp4"):
                video_path = export_path
        output_files = _as_dict(data.get("output_files"))
        folders = _as_dict(output_files.get("folders"))
        finals = folders.get("final") or []
        if not video_path and finals:
            video_path = str(finals[0])
        if video_path and Path(video_path).is_file():
            st.video(video_path)
            st.caption(video_path)
        else:
            source_type = str(
                data.get("source_type")
                or _as_dict(data.get("job")).get("source_type")
                or "script"
            ).lower()
            if source_type == "script":
                st.info("No MP4 was requested for this script-only run.")
            else:
                render_pack = _as_dict(data.get("render_pack"))
                plan = _as_dict(render_pack.get("plan"))
                st.error(
                    str(
                        plan.get("notes")
                        or render_pack.get("notes")
                        or "The media job did not produce an MP4."
                    )
                )
        thumbs = folders.get("thumbnails") or []
        for t in thumbs[:3]:
            if Path(str(t)).is_file():
                st.image(str(t), caption=str(t), use_container_width=True)

    with tabs[5]:
        report = data.get("quality_report") or _as_dict(
            data.get("quality_pack")
        ).get("report")
        report = _as_dict(report)
        if report:
            st.markdown(
                f"**passed:** `{report.get('passed')}` · "
                f"**skipped:** `{report.get('skipped')}`"
            )
            checks = report.get("checks") or []
            if checks:
                rows = []
                for c in checks:
                    if not isinstance(c, dict):
                        continue
                    rows.append(
                        {
                            "id": c.get("id"),
                            "passed": c.get("passed"),
                            "expected": c.get("expected"),
                            "actual": c.get("actual"),
                            "message": c.get("message"),
                        }
                    )
                if rows:
                    st.dataframe(rows, use_container_width=True)
            if report.get("notes"):
                st.caption(str(report["notes"]))
        else:
            st.info("No quality report.")

    with tabs[6]:
        if project_dir:
            root = Path(project_dir)
            interesting = [
                "project.json",
                "transcript.json",
                "scenes.json",
                "analysis.json",
                "moments.json",
                "clips.json",
                "localization.json",
                "video_plan.json",
                "quality_report.json",
                "exports/manifest.json",
            ]
            for rel in interesting:
                p = root / rel
                st.write(("✅" if p.is_file() else "⚪") + f" `{rel}`")
            aliases = _as_dict(output_files.get("aliases"))
            if aliases:
                with st.expander("output_files.aliases"):
                    st.json(aliases)
        export_pack = _as_dict(data.get("export_pack"))
        if export_pack:
            with st.expander("export_pack"):
                st.json(export_pack)
