"""YouTube source metadata schemas for the YouTube Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class YouTubeSourceStatus(str, Enum):
    """Lifecycle status for a YouTube source package."""

    VALIDATED = "validated"
    METADATA_READY = "metadata_ready"
    AWAITING_AUTHORIZED_MEDIA = "awaiting_authorized_media"
    READY_FOR_PIPELINE = "ready_for_pipeline"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class YouTubeSourceMetadata(BaseModel):
    """Stored YouTube source metadata (no claim of unrestricted download)."""

    url: str
    canonical_url: str = ""
    video_id: str = ""
    title: str = ""
    channel: str = ""
    duration_seconds: float | None = None
    source_status: YouTubeSourceStatus = YouTubeSourceStatus.VALIDATED
    provider: str = ""
    fetched_at: datetime = Field(default_factory=_utc_now)
    notes: str = ""


class PreparedYouTubeSource(BaseModel):
    """Result of preparing the project source/ directory."""

    source_dir: str
    metadata_path: str
    local_media_path: str | None = None
    metadata: YouTubeSourceMetadata


class YouTubeAgentResult(BaseModel):
    """LangGraph-friendly return from the YouTube Agent."""

    metadata: YouTubeSourceMetadata
    source_dir: str
    metadata_path: str
    local_media_path: str | None = None
    messages: list[str] = Field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        """Partial WorkflowState update."""
        source_metadata = self.metadata.model_dump(mode="json")
        if self.local_media_path:
            source_metadata["local_media_path"] = self.local_media_path
        return {
            "source_metadata": source_metadata,
            "source_dir": self.source_dir,
            "messages": list(self.messages),
        }
