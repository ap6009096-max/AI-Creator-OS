"""AI Employee Team schemas."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class EmployeeRole(BaseModel):
    name: str
    title: str
    responsibilities: list[str]
    inputs: list[str]
    outputs: list[str]


class ResearchBrief(BaseModel):
    core_topic: str = ""
    target_audience_insights: str = ""
    key_facts_and_stats: list[str] = Field(default_factory=list)
    competitor_angles: list[str] = Field(default_factory=list)
    recommended_content_pillars: list[str] = Field(default_factory=list)


class StrategyPlan(BaseModel):
    content_angle: str = ""
    pacing_style: str = "Fast-Paced & Energetic"
    visual_theme: str = "Modern SaaS Dark"
    hook_strategy: str = ""
    target_platforms: list[str] = Field(default_factory=lambda: ["YouTube", "LinkedIn", "Instagram", "X"])
    call_to_action: str = ""


class ScriptCue(BaseModel):
    timestamp_estimate: str = "00:00"
    speaker: str = "Host"
    spoken_text: str = ""
    visual_cue: str = ""
    broll_suggestion: str = ""
    on_screen_text: str = ""


class MasterScript(BaseModel):
    title: str = ""
    hook_selected: str = ""
    cues: list[ScriptCue] = Field(default_factory=list)
    full_text: str = ""
    estimated_duration_seconds: float = 60.0


class DirectorScene(BaseModel):
    scene_id: int = 1
    shot_type: str = "Medium Close Up"
    camera_movement: str = "Slow Zoom In"
    visual_description: str = ""
    overlay_graphics: str = ""
    audio_cue: str = ""


class DirectorStoryboard(BaseModel):
    concept: str = ""
    scenes: list[DirectorScene] = Field(default_factory=list)
    color_palette: list[str] = Field(default_factory=lambda: ["#0F172A", "#3B82F6", "#10B981"])
    editing_rhythm: str = "Cut on action every 2-3 seconds"


class EditorRenderManifest(BaseModel):
    video_path: str = ""
    audio_path: str = ""
    subtitle_srt_path: str = ""
    clip_timestamps: list[dict[str, Any]] = Field(default_factory=list)
    broll_tracks: list[str] = Field(default_factory=list)


class SEOPackage(BaseModel):
    main_title: str = ""
    alternative_titles: list[str] = Field(default_factory=list)
    description: str = ""
    primary_keywords: list[str] = Field(default_factory=list)
    secondary_tags: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    thumbnail_text_concepts: list[str] = Field(default_factory=list)


class SocialMediaPack(BaseModel):
    linkedin_post: str = ""
    x_thread: list[str] = Field(default_factory=list)
    instagram_caption: str = ""
    tiktok_caption: str = ""
