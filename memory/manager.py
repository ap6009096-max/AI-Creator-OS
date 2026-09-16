"""Creator Memory Manager — local JSON file-system storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.logging import get_logger
from schemas.memory import CreatorMemoryPack, CreatorMemoryResult, CreatorStyleProfile

logger = get_logger(__name__)

MEMORY_DIR = Path("outputs/creator_memory")


class CreatorMemoryManager:
    """Manages reading, writing, and updating persistent local Creator Memory JSON files."""

    def __init__(self, storage_dir: Path | str = MEMORY_DIR) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, creator_id: str) -> Path:
        slug = "".join(c if c.isalnum() else "_" for c in creator_id.lower())
        return self.storage_dir / f"{slug}.json"

    def load_profile(self, creator_id: str = "default_creator") -> CreatorStyleProfile:
        """Load profile from local JSON file or return default if not found."""
        path = self._get_path(creator_id)
        if not path.exists():
            logger.info("No memory file found for %s, creating default profile.", creator_id)
            profile = CreatorStyleProfile(creator_id=creator_id)
            self.save_profile(profile)
            return profile

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return CreatorStyleProfile.model_validate(data)
        except Exception as exc:
            logger.warning("Error reading memory profile %s: %s. Returning default.", creator_id, exc)
            return CreatorStyleProfile(creator_id=creator_id)

    def save_profile(self, profile: CreatorStyleProfile) -> Path:
        """Save creator profile to local JSON file."""
        path = self._get_path(profile.creator_id)
        data = profile.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("Saved Creator Memory Profile for %s to %s", profile.creator_id, path)
        return path

    def update_from_project(
        self, creator_id: str, topic: str, hook_used: str | None = None
    ) -> CreatorStyleProfile:
        """Auto-learn and update creator memory based on completed project."""
        profile = self.load_profile(creator_id)
        if topic and topic not in profile.past_top_topics:
            profile.past_top_topics.append(topic)
            # Keep top 20 topics
            profile.past_top_topics = profile.past_top_topics[-20:]

        if hook_used and hook_used not in profile.preferred_hooks:
            profile.preferred_hooks.append(hook_used)
            profile.preferred_hooks = profile.preferred_hooks[-15:]

        self.save_profile(profile)
        return profile

    def run(self, creator_id: str = "default_creator") -> CreatorMemoryResult:
        """LangGraph node execution wrapper."""
        profile = self.load_profile(creator_id)
        path = str(self._get_path(creator_id))
        pack = CreatorMemoryPack(
            profile=profile,
            notes=f"Loaded memory profile '{profile.channel_name}' for '{creator_id}'.",
        )
        messages = [f"[creator_memory] Successfully loaded memory profile from {path}"]
        return CreatorMemoryResult(memory_pack=pack, memory_path=path, messages=messages)
