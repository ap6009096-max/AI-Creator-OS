"""Audio normalization and stream helpers."""

from __future__ import annotations

from pathlib import Path

from tools.ffmpeg.probe import probe_media
from tools.ffmpeg.runner import ok_output, run_ffmpeg


def normalize_loudness(
    media_path: str | Path,
    output_path: str | Path,
) -> Path | None:
    """Apply loudnorm when audio exists."""
    media = Path(media_path)
    out = Path(output_path)
    if not media.is_file():
        return None
    info = probe_media(media)
    if not info or not info.get("has_audio"):
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = run_ffmpeg(
        [
            "-i",
            str(media.resolve()),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:v",
            "copy",
            str(out.resolve()),
        ]
    )
    return ok_output(out) if ok else None


def ensure_audio_stream(media_path: str | Path) -> bool:
    info = probe_media(media_path)
    return bool(info and info.get("has_audio"))
