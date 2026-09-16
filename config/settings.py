"""Environment-backed application settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    parallel_api_key: str = Field(default="", alias="PARALLEL_API_KEY")
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")
    ffmpeg_path: str = Field(default="", alias="FFMPEG_PATH")
    output_dir: str = Field(default="outputs", alias="OUTPUT_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_env: str = Field(default="development", alias="APP_ENV")
    max_upload_mb: int = Field(default=500, alias="MAX_UPLOAD_MB")
    youtube_api_key: str = Field(default="", alias="YOUTUBE_API_KEY")
    youtube_download_enabled: bool = Field(default=False, alias="YOUTUBE_DOWNLOAD_ENABLED")
    gemini_model: str = Field(default="gemini-3.6-flash", alias="GEMINI_MODEL")
    tts_provider: str = Field(default="", alias="TTS_PROVIDER")
    analysis_sample_fps: float = Field(default=1.0, alias="ANALYSIS_SAMPLE_FPS")
    analysis_scene_threshold: float = Field(default=0.35, alias="ANALYSIS_SCENE_THRESHOLD")
    analysis_max_frames: int = Field(default=900, alias="ANALYSIS_MAX_FRAMES")
    scene_min_duration: float = Field(default=1.5, alias="SCENE_MIN_DURATION")
    scene_min_gap: float = Field(default=0.4, alias="SCENE_MIN_GAP")
    scene_max_scenes: int = Field(default=120, alias="SCENE_MAX_SCENES")
    scene_speaker_gap: float = Field(default=1.25, alias="SCENE_SPEAKER_GAP")
    audio_pause_gap: float = Field(default=0.6, alias="AUDIO_PAUSE_GAP")
    audio_volume_spike_db: float = Field(default=6.0, alias="AUDIO_VOLUME_SPIKE_DB")
    audio_max_events: int = Field(default=200, alias="AUDIO_MAX_EVENTS")
    speaker_turn_gap: float = Field(default=0.8, alias="SPEAKER_TURN_GAP")
    moment_min_score: float = Field(default=0.35, alias="MOMENT_MIN_SCORE")
    moment_max_per_category: int = Field(default=40, alias="MOMENT_MAX_PER_CATEGORY")
    moment_min_duration: float = Field(default=1.0, alias="MOMENT_MIN_DURATION")
    moment_merge_gap: float = Field(default=0.75, alias="MOMENT_MERGE_GAP")
    funny_min_humor_score: float = Field(default=0.4, alias="FUNNY_MIN_HUMOR_SCORE")
    funny_max_moments: int = Field(default=50, alias="FUNNY_MAX_MOMENTS")
    funny_setup_window: float = Field(default=4.0, alias="FUNNY_SETUP_WINDOW")
    funny_laughter_weight: float = Field(default=0.25, alias="FUNNY_LAUGHTER_WEIGHT")
    viral_min_final_score: float = Field(default=0.4, alias="VIRAL_MIN_FINAL_SCORE")
    viral_max_moments: int = Field(default=40, alias="VIRAL_MAX_MOMENTS")
    viral_window_pad: float = Field(default=1.5, alias="VIRAL_WINDOW_PAD")
    clip_target_duration: int = Field(default=30, alias="CLIP_TARGET_DURATION")
    clip_duration_tolerance: float = Field(default=0.35, alias="CLIP_DURATION_TOLERANCE")
    clip_max_clips: int = Field(default=20, alias="CLIP_MAX_CLIPS")
    clip_max_overlap: float = Field(default=0.35, alias="CLIP_MAX_OVERLAP")
    clip_min_score: float = Field(default=0.35, alias="CLIP_MIN_SCORE")

    @property
    def has_gemini_api_key(self) -> bool:
        """Return True when a non-empty Gemini API key is configured."""
        return bool(self.gemini_api_key.strip())

    @property
    def has_parallel_api_key(self) -> bool:
        """Return True when a Parallel Search API key is configured."""
        return bool(self.parallel_api_key.strip())

    @property
    def has_youtube_api_key(self) -> bool:
        """Return True when a YouTube Data API key is configured."""
        return bool(self.youtube_api_key.strip())

    @property
    def has_tts_provider(self) -> bool:
        """Return True when a non-passthrough TTS provider name is configured."""
        raw = (self.tts_provider or "").strip().lower()
        return bool(raw) and raw not in {"passthrough", "none", "null"}

    def require_gemini_api_key(self) -> str:
        """Return the Gemini API key or raise if missing.

        Used by later prompts that call Gemini; foundation does not invoke this yet.
        """
        from core.errors import ConfigurationError

        key = self.gemini_api_key.strip()
        if not key:
            raise ConfigurationError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        return key


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
