"""Schemas for video generation jobs, feature flags, and pipeline progress."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from schemas.localization import LocalizationTarget

ALLOWED_UPLOAD_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

TargetClipDuration = Literal[15, 30, 45, 60, 90]

HumorAdaptationMode = Literal["original", "localized", "regional", "none"]

PIPELINE_STEPS: tuple[str, ...] = (
    "Source detected",
    "Video loaded",
    "Transcript extracted",
    "Scenes detected",
    "Audio analyzed",
    "Important moments found",
    "Funny moments found",
    "Viral moments found",
    "Clips selected",
    "Story generated",
    "Localization completed",
    "Captions generated",
    "Video rendered",
    "Quality checked",
    "Export completed",
)


class SourceType(str, Enum):
    YOUTUBE = "youtube"
    UPLOAD = "upload"
    SCRIPT = "script"


class ProgressStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FeatureFlags(BaseModel):
    """Feature toggles for the video generation pipeline."""

    smart_clip_detection: bool = True
    viral_moments: bool = True
    funny_moments: bool = False
    emotional_moments: bool = False
    educational_moments: bool = False
    surprise_moments: bool = False
    important_moments: bool = True
    reaction_moments: bool = False
    inspirational_moments: bool = False
    cinematic_moments: bool = False
    expert_insights: bool = False
    best_quotes: bool = False
    b_roll: bool = False
    captions: bool = True
    voice: bool = False
    music: bool = False
    cultural_adaptation: bool = False
    regional_humor: bool = False
    smart_reframing: bool = False
    platform_optimization: bool = True
    enable_research: bool = True


class VideoJobConfig(BaseModel):
    """Creative and localization configuration for a job."""

    video_type: str = "Shorts"
    visual_style: str = "Cinematic"
    environment: str = "Wildlife/Nature Forest"
    country: str = "United States"
    region: str = "Global"
    language: str = "English"
    audience: str = "General"
    voice: str = "Original Voice"
    humor_style: str = "None"
    humor_adaptation: HumorAdaptationMode = "none"
    platform: str = "YouTube Shorts"
    target_clip_duration: TargetClipDuration = 30
    music: str = "Original Audio"
    caption_style: str = "Platform Safe"
    caption_emoji: bool = False
    caption_burn_in: bool = True
    reframe_aspect: str = ""
    localization_targets: list[LocalizationTarget] = Field(default_factory=list)


class ProgressStep(BaseModel):
    """One step in the generation progress panel."""

    id: int
    label: str
    status: ProgressStepStatus = ProgressStepStatus.PENDING


class VideoJobRequest(BaseModel):
    """Full request payload submitted from the Streamlit UI to LangGraph."""

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    source_type: SourceType
    youtube_url: str = ""
    local_media_path: str = ""
    upload_path: str = ""
    script_text: str = ""
    config: VideoJobConfig = Field(default_factory=VideoJobConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    @field_validator("youtube_url")
    @classmethod
    def normalize_youtube_url(cls, value: str) -> str:
        return value.strip()

    @field_validator("script_text")
    @classmethod
    def normalize_script(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_source_payload(self) -> VideoJobRequest:
        if self.source_type == SourceType.YOUTUBE:
            url = self.youtube_url.lower()
            if not self.youtube_url:
                raise ValueError("YouTube URL is required.")
            if "youtube.com" not in url and "youtu.be" not in url:
                raise ValueError("URL must be a valid YouTube link (youtube.com or youtu.be).")
            if self.local_media_path:
                media = Path(self.local_media_path)
                if not media.is_file():
                    raise ValueError(f"Authorized local media file not found: {media}")
                if media.suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
                    raise ValueError(
                        f"Unsupported local media format '{media.suffix.lower()}'. "
                        f"Allowed: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
                    )
        elif self.source_type == SourceType.UPLOAD:
            if not self.upload_path:
                raise ValueError("Uploaded video path is required.")
            ext = Path(self.upload_path).suffix.lower()
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                raise ValueError(
                    f"Unsupported upload format '{ext}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
                )
        elif self.source_type == SourceType.SCRIPT:
            if not self.script_text:
                raise ValueError("Script text is required.")
        return self


def initial_progress_steps() -> list[dict[str, Any]]:
    """Return pipeline steps as serializable dicts, all pending."""
    return [
        ProgressStep(id=i, label=label).model_dump(mode="json")
        for i, label in enumerate(PIPELINE_STEPS)
    ]
