"""Abstract YouTube source provider interface."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from schemas.youtube import PreparedYouTubeSource, YouTubeSourceMetadata


@runtime_checkable
class YouTubeSourceProvider(Protocol):
    """Swap-friendly interface for YouTube metadata and source preparation.

    Implementations must not bypass platform restrictions. Binary media download
    belongs only in authorized provider integrations added later.
    """

    name: str

    def normalize_url(self, url: str) -> str:
        """Return a canonical YouTube watch URL."""
        ...

    def fetch_metadata(self, url: str) -> YouTubeSourceMetadata:
        """Fetch available metadata through authorized APIs only."""
        ...

    def prepare_source(
        self,
        project_dir: str | Path,
        metadata: YouTubeSourceMetadata,
    ) -> PreparedYouTubeSource:
        """Write source/ artifacts without downloading restricted media bytes."""
        ...


def get_youtube_provider() -> YouTubeSourceProvider:
    """Return the default YouTube provider (oEmbed + optional Data API)."""
    from tools.youtube.oembed_provider import OEmbedYouTubeProvider

    return OEmbedYouTubeProvider()
