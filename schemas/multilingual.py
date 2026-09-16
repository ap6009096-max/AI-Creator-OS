"""Multilingual Content Factory schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class LocalizedContentItem(BaseModel):
    language_code: str  # en, hi, es, fr, de, ar
    language_name: str
    translated_title: str = ""
    translated_script: str = ""
    translated_captions_srt: str = ""
    translated_seo_tags: list[str] = Field(default_factory=list)


class MultilingualContentPack(BaseModel):
    source_language: str = "en"
    localizations: dict[str, LocalizedContentItem] = Field(default_factory=dict)


class MultilingualResult(BaseModel):
    localized_packages: MultilingualContentPack
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "localized_packages": self.localized_packages.model_dump(mode="json"),
            "messages": list(self.messages),
        }
