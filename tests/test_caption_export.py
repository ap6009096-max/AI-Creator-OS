"""Tests for SRT / VTT / ASS caption export."""

from __future__ import annotations

from schemas.captions import CaptionCue, CaptionTrack
from tools.captions.catalog import default_caption_style, resolve_caption_style, resolve_safe_area
from tools.captions.export import ass_is_useful, render_ass, render_srt, render_vtt


CUES = [
    CaptionCue(level="sentence", start=0.0, end=1.5, text="Hello world"),
    CaptionCue(level="sentence", start=1.5, end=3.0, text="Second line"),
]


def test_render_srt() -> None:
    srt = render_srt(CUES)
    assert "1\n" in srt
    assert "00:00:00,000 --> 00:00:01,500" in srt
    assert "Hello world" in srt
    assert "00:00:01,500 --> 00:00:03,000" in srt


def test_render_vtt() -> None:
    vtt = render_vtt(CUES)
    assert vtt.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:01.500" in vtt
    assert "Hello world" in vtt


def test_render_ass_includes_safe_margins() -> None:
    style = resolve_caption_style("Platform Safe") or default_caption_style()
    safe = resolve_safe_area("TikTok")
    assert safe is not None
    track = CaptionTrack(language="en", cues=CUES)
    ass = render_ass(track, style, safe)
    assert "[Script Info]" in ass
    assert "Dialogue:" in ass
    assert str(safe.margin_v) in ass
    assert "Hello world" in ass


def test_ass_useful_for_burn_in_and_animation() -> None:
    minimal = resolve_caption_style("Minimal")
    kinetic = resolve_caption_style("Kinetic")
    assert minimal is not None and kinetic is not None
    assert ass_is_useful(minimal, burn_in=True) is True
    assert ass_is_useful(minimal, burn_in=False) is False
    assert ass_is_useful(kinetic, burn_in=False) is True
