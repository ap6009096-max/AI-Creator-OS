"""Thin wrapper around the Parallel Search API (parallel-web SDK)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config.settings import get_settings
from core.errors import ConfigurationError, ResearchAgentError
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParallelSearchResult:
    objective: str
    search_queries: list[str]
    results: list[dict[str, Any]] = field(default_factory=list)
    raw: Any | None = None


def run_parallel_search(
    *,
    objective: str,
    search_queries: list[str],
    mode: str = "turbo",
    api_key: str | None = None,
    client: Any | None = None,
) -> ParallelSearchResult:
    """Execute Parallel Search and normalize title/url/excerpts."""
    queries = [q.strip() for q in search_queries if str(q).strip()]
    if not queries:
        raise ResearchAgentError("Parallel Search requires at least one search query.")

    key = (api_key if api_key is not None else get_settings().parallel_api_key).strip()
    if client is None and not key:
        raise ConfigurationError(
            "PARALLEL_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    try:
        if client is None:
            from parallel import Parallel

            client = Parallel(api_key=key)
        response = client.search(
            objective=objective or queries[0],
            search_queries=queries[:3],
            mode=mode,
        )
    except ConfigurationError:
        raise
    except ResearchAgentError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Parallel Search failed")
        raise ResearchAgentError(f"Parallel Search failed: {exc}") from exc

    hits: list[dict[str, Any]] = []
    for item in getattr(response, "results", None) or []:
        title = str(getattr(item, "title", "") or "")
        url = str(getattr(item, "url", "") or "")
        excerpts_raw = getattr(item, "excerpts", None) or []
        excerpts = [str(e) for e in excerpts_raw if str(e).strip()]
        if isinstance(item, dict):
            title = str(item.get("title") or title)
            url = str(item.get("url") or url)
            excerpts = [str(e) for e in (item.get("excerpts") or excerpts) if str(e).strip()]
        hits.append({"title": title, "url": url, "excerpts": excerpts})

    return ParallelSearchResult(
        objective=objective or queries[0],
        search_queries=queries[:3],
        results=hits,
        raw=response,
    )
