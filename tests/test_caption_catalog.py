"""Tests for caption style / platform safe-area catalog."""

from __future__ import annotations

from tools.captions.catalog import (
    list_caption_styles,
    list_platform_safe_areas,
    resolve_caption_style,
    resolve_safe_area,
)


def test_catalog_loads_styles() -> None:
    styles = list_caption_styles()
    names = {s.name for s in styles}
    for required in ("Platform Safe", "Minimal", "Pop", "Kinetic", "High Contrast"):
        assert required in names


def test_catalog_loads_platforms() -> None:
    areas = list_platform_safe_areas()
    names = {a.name for a in areas}
    assert "YouTube Shorts" in names
    assert "TikTok" in names
    tiktok = resolve_safe_area("TikTok")
    assert tiktok is not None
    assert tiktok.margin_v >= 180


def test_resolve_caption_style() -> None:
    kinetic = resolve_caption_style("Kinetic")
    assert kinetic is not None
    assert kinetic.animation == "word_highlight"
    safe = resolve_caption_style("platform safe")
    assert safe is not None
    assert safe.name == "Platform Safe"
