"""Tests for localization catalog resolution."""

from __future__ import annotations

from tools.localization.catalog import (
    build_locale_pack,
    expand_targets,
    resolve_country,
    resolve_language,
    resolve_region,
)
from schemas.localization import LocalizationTarget


def test_india_default_hindi() -> None:
    country = resolve_country("India")
    assert country is not None
    assert country.default_language == "Hindi"
    assert country.currency.code == "INR"
    pack = build_locale_pack(LocalizationTarget(country="India", language="Hindi"))
    assert pack.language is not None
    assert pack.language.name == "Hindi"


def test_india_gujarat_gujarati() -> None:
    country = resolve_country("India")
    region = resolve_region("Gujarat", country=country)
    assert region is not None
    assert region.language == "Gujarati"
    lang = resolve_language("Gujarati")
    assert lang is not None
    assert lang.code == "gu"
    pack = build_locale_pack(
        LocalizationTarget(country="India", region="Gujarat", language="Gujarati")
    )
    assert pack.region is not None
    assert pack.region.name == "Gujarat"
    assert pack.language is not None
    assert pack.language.name == "Gujarati"


def test_usa_english() -> None:
    country = resolve_country("United States")
    assert country is not None
    assert country.default_language == "English"
    assert country.measurements == "imperial"
    pack = build_locale_pack(
        LocalizationTarget(country="United States", language="English")
    )
    assert pack.language is not None
    assert pack.language.code == "en"


def test_japan_japanese() -> None:
    country = resolve_country("Japan")
    assert country is not None
    assert country.default_language == "Japanese"
    pack = build_locale_pack(LocalizationTarget(country="Japan", language="Japanese"))
    assert pack.language is not None
    assert pack.language.name == "Japanese"


def test_continental_region_is_none() -> None:
    country = resolve_country("India")
    assert resolve_region("Asia", country=country) is None
    assert resolve_region("Global", country=country) is None


def test_expand_targets_cultural_adaptation() -> None:
    targets = expand_targets(
        country="India",
        region="Gujarat",
        language="English",
        cultural_adaptation=True,
    )
    langs = {t.language for t in targets}
    assert "English" in langs
    assert "Hindi" in langs
    assert "Gujarati" in langs
    assert len(targets) >= 2


def test_expand_targets_primary_only() -> None:
    targets = expand_targets(
        country="Japan",
        region="Global",
        language="Japanese",
        cultural_adaptation=False,
    )
    assert len(targets) == 1
    assert targets[0].language == "Japanese"
    assert targets[0].region == ""
