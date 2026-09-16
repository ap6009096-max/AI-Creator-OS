"""Map LangGraph nodes to creator-facing production stages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ProductionStage:
    id: str
    label: str
    description: str
    order: int


STAGES: tuple[ProductionStage, ...] = (
    ProductionStage("understand", "Understand", "Input detection & analysis", 1),
    ProductionStage("research", "Research", "Parallel Search + Gemini grounding", 2),
    ProductionStage("plan", "Plan", "Story strategy", 3),
    ProductionStage("create", "Create", "Script + storyboard", 4),
    ProductionStage("produce", "Produce", "Video, audio, captions", 5),
    ProductionStage("review", "Review", "Quality + analytics", 6),
    ProductionStage("export", "Export", "Package deliverables", 7),
)

STAGE_BY_ID: dict[str, ProductionStage] = {s.id: s for s in STAGES}

# LangGraph node name → stage id
NODE_TO_STAGE: dict[str, str] = {
    "supervisor": "understand",
    "input_agent": "understand",
    "youtube_ingest": "understand",
    "local_video_ingest": "understand",
    "script_ingest": "understand",
    "step_02_transcript_extracted": "understand",
    "video_understanding": "understand",
    "scene_detection": "understand",
    "audio_analysis": "understand",
    "speaker_analysis": "understand",
    "moment_detection": "understand",
    "funny_moment": "understand",
    "viral_moment": "understand",
    "smart_clip": "understand",
    "skip_funny": "understand",
    "skip_viral": "understand",
    "research": "research",
    "skip_research": "research",
    "story": "plan",
    "script": "create",
    "storyboard": "create",
    "country": "produce",
    "regional": "produce",
    "language": "produce",
    "cultural": "produce",
    "humor": "produce",
    "skip_cultural": "produce",
    "skip_humor": "produce",
    "video_type": "produce",
    "visual_style": "produce",
    "environment": "produce",
    "b_roll": "produce",
    "voice": "produce",
    "music": "produce",
    "captions": "produce",
    "smart_reframe": "produce",
    "platform": "produce",
    "skip_broll": "produce",
    "skip_voice": "produce",
    "skip_music": "produce",
    "render": "produce",
    "quality": "review",
    "quality_retry": "review",
    "analytics": "review",
    "export": "export",
}

NODE_LABELS: dict[str, str] = {
    "supervisor": "Supervisor → workflow initialized",
    "input_agent": "Input Agent → source detected",
    "youtube_ingest": "YouTube Agent → source packaged",
    "local_video_ingest": "Ingest Agent → media loaded",
    "script_ingest": "Text Agent → script analyzed",
    "video_understanding": "Analysis Agent → content analyzed",
    "scene_detection": "Scene Agent → scenes detected",
    "audio_analysis": "Audio Agent → audio analyzed",
    "speaker_analysis": "Speaker Agent → speakers mapped",
    "moment_detection": "Moment Agent → moments found",
    "smart_clip": "Clip Agent → clips selected",
    "research": "Research Agent → sources collected",
    "skip_research": "Research Agent → skipped",
    "story": "Planning Agent → story strategy generated",
    "script": "Script Agent → script generated",
    "storyboard": "Storyboard Agent → scenes created",
    "country": "Localization → country resolved",
    "language": "Localization → language adapted",
    "video_type": "Production → video type set",
    "captions": "Production → captions generated",
    "platform": "Optimize → platform pack ready",
    "render": "Production → video rendered",
    "quality": "QA Agent → quality checked",
    "analytics": "Analytics Agent → rollup complete",
    "export": "Export Agent → package ready",
}


def stage_for_node(node: str) -> str | None:
    if node in NODE_TO_STAGE:
        return NODE_TO_STAGE[node]
    # transcript node is dynamic slug
    if "transcript" in node:
        return "understand"
    if node.endswith("_failed") or node.startswith("skip_"):
        base = node.replace("_failed", "").replace("skip_", "")
        return NODE_TO_STAGE.get(base) or NODE_TO_STAGE.get(node)
    return None


def infer_active_node(state: dict[str, Any]) -> str | None:
    """Best-effort active node from messages / next_agent."""
    next_agent = state.get("next_agent")
    if isinstance(next_agent, str) and next_agent:
        return next_agent
    messages = state.get("messages") or []
    for msg in reversed(messages):
        text = str(msg)
        if text.startswith("[") and "]" in text:
            name = text[1 : text.index("]")]
            if name:
                return name
    return None


def stage_statuses_from_state(state: dict[str, Any]) -> dict[str, str]:
    """Return stage_id → pending|running|completed|failed."""
    statuses = {s.id: "pending" for s in STAGES}
    active = infer_active_node(state)
    active_stage = stage_for_node(active) if active else None

    # Heuristics from presence of artifacts
    artifacts = [
        ("understand", bool(state.get("project") or state.get("clips") or state.get("analysis"))),
        ("research", state.get("research") is not None),
        ("plan", state.get("stories") is not None),
        ("create", bool(state.get("scripts") or state.get("storyboard"))),
        ("produce", bool(state.get("render_pack") or state.get("captions_pack") or state.get("platform_pack"))),
        ("review", bool(state.get("quality_pack") or state.get("analytics"))),
        ("export", state.get("export_pack") is not None),
    ]

    job_failed = state.get("status") == "failed"
    reached_running = False
    for stage_id, ready in artifacts:
        if ready:
            statuses[stage_id] = "completed"
        elif active_stage == stage_id:
            statuses[stage_id] = "failed" if job_failed else "running"
            reached_running = True
        elif not reached_running and active_stage:
            # stages before active that aren't ready stay pending unless earlier completed
            pass

    # Mark stages before the first incomplete as completed when later ones exist
    last_completed = -1
    for s in STAGES:
        if statuses[s.id] == "completed":
            last_completed = s.order
    for s in STAGES:
        if s.order < last_completed and statuses[s.id] == "pending":
            statuses[s.id] = "completed"
        if active_stage == s.id and statuses[s.id] != "completed":
            statuses[s.id] = "failed" if job_failed else "running"

    if state.get("status") == "completed":
        for s in STAGES:
            statuses[s.id] = "completed"

    return statuses


def activity_lines_from_messages(
    messages: list[str] | None,
    *,
    limit: int = 40,
) -> list[dict[str, str]]:
    """Convert pipeline messages into timestamped activity rows."""
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    rows: list[dict[str, str]] = []
    for msg in messages or []:
        text = str(msg).strip()
        if not text:
            continue
        label = text
        if text.startswith("[") and "]" in text:
            node = text[1 : text.index("]")]
            pretty = NODE_LABELS.get(node)
            if pretty:
                label = pretty
        rows.append({"time": now, "text": label})
    return rows[-limit:]


def agent_card_from_state(state: dict[str, Any]) -> dict[str, Any]:
    """Compact supervisor/active agent card fields."""
    active = infer_active_node(state) or "supervisor"
    stage = stage_for_node(active) or "understand"
    statuses = stage_statuses_from_state(state)
    completed = sum(1 for v in statuses.values() if v == "completed")
    progress = int(100 * completed / max(len(STAGES), 1))
    status = state.get("status") or "pending"
    running = status == "running"
    return {
        "name": active.replace("_", " ").title() + " Agent",
        "status": "Running" if running else status.replace("_", " ").title(),
        "model": "Gemini",
        "task": STAGE_BY_ID[stage].description if stage in STAGE_BY_ID else "Coordinating workflow",
        "progress": progress,
        "stage": stage,
    }
