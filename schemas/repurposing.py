"""Content Repurposing Engine schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from schemas.employees import SEOPackage, SocialMediaPack


class ShortClipAsset(BaseModel):
    clip_id: str
    title: str
    hook: str
    start_time: str
    end_time: str
    transcript_snippet: str
    vertical_aspect: str = "9:16"


class RepurposedContentPackage(BaseModel):
    project_id: str = ""
    source_title: str = ""
    long_form_summary: str = ""
    shorts_clips: list[ShortClipAsset] = Field(default_factory=list)
    blog_article_md: str = ""
    social_media: SocialMediaPack = Field(default_factory=SocialMediaPack)
    seo_package: SEOPackage = Field(default_factory=SEOPackage)
    captions_srt: str = ""


class RepurposingResult(BaseModel):
    repurposed_package: RepurposedContentPackage
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "repurposed_package": self.repurposed_package.model_dump(mode="json"),
            "messages": list(self.messages),
        }
