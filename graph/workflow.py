"""LangGraph video generation workflow — full multi-agent orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.analytics_agent import AnalyticsAgent
from agents.audio_analysis_agent import AudioAnalysisAgent
from agents.broll_agent import BRollAgent
from agents.caption_agent import CaptionAgent
from agents.country_agent import CountryAgent
from agents.cultural_adaptation_agent import CulturalAdaptationAgent
from agents.environment_agent import EnvironmentAgent
from agents.export_agent import ExportAgent
from agents.funny_moment_agent import FunnyMomentAgent
from agents.humor_localization_agent import HumorLocalizationAgent
from agents.input_agent import InputAgent
from agents.language_agent import LanguageAgent
from agents.local_video_ingest_agent import LocalVideoIngestAgent
from agents.moment_detection_agent import MomentDetectionAgent
from agents.music_agent import MusicAgent
from agents.platform_agent import PlatformAgent
from agents.quality_agent import QualityAgent
from agents.regional_agent import RegionalAgent
from agents.reframe_agent import ReframeAgent
from agents.render_agent import RenderAgent
from agents.research_agent import ResearchAgent
from agents.scene_detection_agent import SceneDetectionAgent
from agents.script_agent import ScriptAgent
from agents.smart_clip_agent import SmartClipAgent
from agents.speaker_analysis_agent import SpeakerAnalysisAgent
from agents.story_agent import StoryAgent
from agents.storyboard_agent import StoryboardAgent
from agents.supervisor_agent import SupervisorAgent
from agents.text_agent import TextAgent
from agents.transcript_agent import TranscriptAgent
from agents.video_type_agent import VideoTypeAgent
from agents.visual_style_agent import VisualStyleAgent
from agents.video_understanding_agent import VideoUnderstandingAgent
from agents.viral_moment_agent import ViralMomentAgent
from agents.voice_agent import VoiceAgent
from agents.youtube_agent import YouTubeAgent
from core.errors import (
    AnalyticsAgentError,
    AudioAnalysisError,
    BRollAgentError,
    CaptionAgentError,
    CountryAgentError,
    CulturalAdaptationError,
    EnvironmentAgentError,
    ExportAgentError,
    FunnyMomentError,
    HumorLocalizationError,
    InputValidationError,
    LanguageAgentError,
    MomentDetectionError,
    MusicAgentError,
    PlatformAgentError,
    QualityAgentError,
    RegionalAgentError,
    ReframeAgentError,
    RenderAgentError,
    ResearchAgentError,
    SceneDetectionError,
    ScriptAgentError,
    SmartClipError,
    SpeakerAnalysisError,
    StorageError,
    StoryAgentError,
    StoryboardAgentError,
    SupervisorAgentError,
    TextAgentError,
    TranscriptAgentError,
    VideoTypeAgentError,
    VisualStyleAgentError,
    VideoUnderstandingError,
    ViralMomentError,
    VoiceAgentError,
    WorkflowError,
    YouTubeAgentError,
)
from core.logging import get_logger
from graph.routers import (
    route_after_broll,
    route_after_cultural,
    route_after_environment,
    route_after_funny,
    route_after_humor,
    route_after_language,
    route_after_moment,
    route_after_music,
    route_after_research,
    route_after_smart_clip_research,
    route_after_speaker,
    route_after_viral,
    route_after_voice,
)
from graph.state_view import project_state_view
from schemas.base import JobStatus
from schemas.job import (
    PIPELINE_STEPS,
    FeatureFlags,
    ProgressStepStatus,
    SourceType,
    VideoJobConfig,
    VideoJobRequest,
    initial_progress_steps,
)
from schemas.project import DownstreamRoute, ProjectMetadata
from tools.project.layout import ensure_project_layout, finalize_project_layout

logger = get_logger(__name__)

OnStepCallback = Callable[[dict[str, Any]], None]

INGEST_NODES: dict[str, str] = {
    DownstreamRoute.YOUTUBE_INGEST.value: "youtube_ingest",
    DownstreamRoute.LOCAL_VIDEO_INGEST.value: "local_video_ingest",
    DownstreamRoute.SCRIPT_INGEST.value: "script_ingest",
}


def _slug(label: str) -> str:
    return (
        label.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )


# No stub pipeline steps remain (14 = Export Agent via render/quality/export)
STUB_STEP_INDICES: tuple[int, ...] = ()
STUB_NODE_NAMES: tuple[str, ...] = ()
TRANSCRIPT_NODE = f"step_02_{_slug(PIPELINE_STEPS[2])}"
UNDERSTANDING_NODE = "video_understanding"
SCENE_DETECTION_NODE = "scene_detection"
AUDIO_ANALYSIS_NODE = "audio_analysis"
SPEAKER_ANALYSIS_NODE = "speaker_analysis"
FUNNY_MOMENT_NODE = "funny_moment"
VIRAL_MOMENT_NODE = "viral_moment"
MOMENT_DETECTION_NODE = "moment_detection"
SMART_CLIP_NODE = "smart_clip"
RESEARCH_NODE = "research"
VIDEO_TYPE_NODE = "video_type"
VISUAL_STYLE_NODE = "visual_style"
ENVIRONMENT_NODE = "environment"
STORY_NODE = "story"
SCRIPT_NODE = "script"
STORYBOARD_NODE = "storyboard"
COUNTRY_NODE = "country"
REGIONAL_NODE = "regional"
CULTURAL_NODE = "cultural"
HUMOR_NODE = "humor"
LANGUAGE_NODE = "language"
BROLL_NODE = "b_roll"
VOICE_NODE = "voice"
MUSIC_NODE = "music"
CAPTIONS_NODE = "captions"
REFRAME_NODE = "smart_reframe"
PLATFORM_NODE = "platform"
RENDER_NODE = "render"
QUALITY_NODE = "quality"
ANALYTICS_NODE = "analytics"
EXPORT_NODE = "export"
SUPERVISOR_NODE = "supervisor"

# Backward-compatible export used by tests (PROMPT 25 order)
STEP_NODE_NAMES: tuple[str, ...] = (
    SUPERVISOR_NODE,
    "input_agent",
    "youtube_ingest",
    "local_video_ingest",
    "script_ingest",
    TRANSCRIPT_NODE,
    UNDERSTANDING_NODE,
    SCENE_DETECTION_NODE,
    AUDIO_ANALYSIS_NODE,
    SPEAKER_ANALYSIS_NODE,
    MOMENT_DETECTION_NODE,
    FUNNY_MOMENT_NODE,
    VIRAL_MOMENT_NODE,
    SMART_CLIP_NODE,
    RESEARCH_NODE,
    STORY_NODE,
    SCRIPT_NODE,
    STORYBOARD_NODE,
    COUNTRY_NODE,
    REGIONAL_NODE,
    LANGUAGE_NODE,
    CULTURAL_NODE,
    HUMOR_NODE,
    VIDEO_TYPE_NODE,
    VISUAL_STYLE_NODE,
    ENVIRONMENT_NODE,
    BROLL_NODE,
    VOICE_NODE,
    MUSIC_NODE,
    CAPTIONS_NODE,
    REFRAME_NODE,
    PLATFORM_NODE,
    RENDER_NODE,
    QUALITY_NODE,
    ANALYTICS_NODE,
    EXPORT_NODE,
)


class WorkflowState(TypedDict):
    """LangGraph state for the video generation pipeline."""

    job: dict[str, Any]
    status: str
    current_step: int
    steps: list[dict[str, Any]]
    messages: list[str]
    error: str | None
    result: dict[str, Any] | None
    project: dict[str, Any] | None
    project_dir: str | None
    next_agent: str | None
    source_metadata: dict[str, Any] | None
    source_dir: str | None
    transcript: dict[str, Any] | None
    speech_transcript: dict[str, Any] | None
    analysis: dict[str, Any] | None
    scenes: dict[str, Any] | None
    audio_analysis: dict[str, Any] | None
    speakers: dict[str, Any] | None
    funny_moments: dict[str, Any] | None
    viral_moments: dict[str, Any] | None
    moments: dict[str, Any] | None
    clips: dict[str, Any] | None
    research: dict[str, Any] | None
    supervisor: dict[str, Any] | None
    storyboard: dict[str, Any] | None
    analytics: dict[str, Any] | None
    video_type_pack: dict[str, Any] | None
    visual_style_pack: dict[str, Any] | None
    environment_pack: dict[str, Any] | None
    stories: dict[str, Any] | None
    scripts: dict[str, Any] | None
    country_profile: dict[str, Any] | None
    region_profile: dict[str, Any] | None
    locale_pack: dict[str, Any] | None
    cultural_adaptation: dict[str, Any] | None
    humor_localization: dict[str, Any] | None
    localizations: dict[str, Any] | None
    broll_pack: dict[str, Any] | None
    voice_pack: dict[str, Any] | None
    music_pack: dict[str, Any] | None
    captions_pack: dict[str, Any] | None
    reframe_pack: dict[str, Any] | None
    platform_pack: dict[str, Any] | None
    render_pack: dict[str, Any] | None
    quality_pack: dict[str, Any] | None
    export_pack: dict[str, Any] | None
    quality_retry_count: int
    stop_after_storyboard: bool

    # New Creator OS Extensions
    creator_profile_id: str
    creator_memory: dict[str, Any] | None
    viral_analysis: dict[str, Any] | None
    research_brief: dict[str, Any] | None
    content_strategy: dict[str, Any] | None
    master_script: dict[str, Any] | None
    director_storyboard: dict[str, Any] | None
    rendered_assets: dict[str, Any] | None
    seo_package: dict[str, Any] | None
    social_media_pack: dict[str, Any] | None
    repurposed_package: dict[str, Any] | None
    qa_report: dict[str, Any] | None
    qa_retry_count: int
    calendar_plan: dict[str, Any] | None
    localized_packages: dict[str, Any] | None


def _supervisor_node(state: WorkflowState) -> dict[str, Any]:
    """Supervisor Agent: validate job and record execution plan metadata."""
    try:
        result = SupervisorAgent().run(state.get("job") or {})
    except SupervisorAgentError as exc:
        messages = list(state.get("messages") or [])
        messages.append(f"[supervisor] Failed: {exc}")
        return {
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "supervisor": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_supervisor(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "supervisor_failed"
    return "continue"


def _supervisor_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Supervisor planning failed",
    }


def _mark_steps_completed(
    steps: list[dict[str, Any]],
    completed_through: int,
) -> list[dict[str, Any]]:
    """Return a copy of steps with indices <= completed_through marked completed."""
    updated = [dict(s) for s in steps]
    for i, step in enumerate(updated):
        if i <= completed_through:
            step["status"] = ProgressStepStatus.COMPLETED.value
        else:
            step["status"] = ProgressStepStatus.PENDING.value
    return updated


def _input_agent_node(state: WorkflowState) -> dict[str, Any]:
    """Real Input Agent: validate, create project, route downstream."""
    try:
        request = VideoJobRequest.model_validate(state.get("job") or {})
        result = InputAgent().run(request)
    except InputValidationError as exc:
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        if steps:
            steps[0]["status"] = ProgressStepStatus.FAILED.value
        messages = list(state.get("messages") or [])
        messages.append(f"[input] Validation failed: {exc}")
        return {
            "current_step": 0,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "project": None,
            "project_dir": None,
            "next_agent": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=0,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)

    return {
        **result.to_state_dict(),
        "current_step": 0,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _local_video_ingest_node(state: WorkflowState) -> dict[str, Any]:
    """Real local upload ingest: copy into source/, probe duration."""
    project_raw = state.get("project") or {}
    job = state.get("job") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = LocalVideoIngestAgent().run(
            project,
            project_dir=state.get("project_dir"),
            upload_path=job.get("upload_path") or project.source_path,
        )
        # Ensure layout folders early
        if state.get("project_dir"):
            ensure_project_layout(state["project_dir"])
    except (InputValidationError, StorageError) as exc:
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        steps = _mark_steps_completed(steps, completed_through=0)
        if len(steps) > 1:
            steps[1]["status"] = ProgressStepStatus.FAILED.value
        messages = list(state.get("messages") or [])
        messages.append(f"[local_video_ingest] Failed: {exc}")
        return {
            "current_step": 1,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "source_metadata": None,
            "source_dir": None,
        }
    except Exception as exc:  # noqa: BLE001
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        steps = _mark_steps_completed(steps, completed_through=0)
        if len(steps) > 1:
            steps[1]["status"] = ProgressStepStatus.FAILED.value
        messages = list(state.get("messages") or [])
        messages.append(f"[local_video_ingest] Failed: {exc}")
        return {
            "current_step": 1,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "source_metadata": None,
            "source_dir": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=1,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 1,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_local_video(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "local_video_failed"
    return "continue"


def _local_video_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Local video ingest failed",
    }

def _youtube_ingest_node(state: WorkflowState) -> dict[str, Any]:
    """Real YouTube Agent: metadata + source/ package (no unrestricted download)."""
    project_raw = state.get("project") or {}
    project_dir = state.get("project_dir")
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = YouTubeAgent().run(project, project_dir=project_dir)
    except YouTubeAgentError as exc:
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        steps = _mark_steps_completed(steps, completed_through=0)
        if len(steps) > 1:
            steps[1]["status"] = ProgressStepStatus.FAILED.value
        messages = list(state.get("messages") or [])
        messages.append(f"[youtube] Failed: {exc}")
        return {
            "current_step": 1,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "source_metadata": None,
            "source_dir": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=1,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 1,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_youtube(state: WorkflowState) -> str:
    """Continue pipeline or stop after YouTube ingest."""
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "youtube_failed"
    return "continue"


def _script_ingest_node(state: WorkflowState) -> dict[str, Any]:
    """Real Text Agent: structured transcript.json for script input."""
    project_raw = state.get("project") or {}
    project_dir = state.get("project_dir")
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = TextAgent().run(project, project_dir=project_dir)
    except TextAgentError as exc:
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        steps = _mark_steps_completed(steps, completed_through=0)
        if len(steps) > 1:
            steps[1]["status"] = ProgressStepStatus.FAILED.value
        messages = list(state.get("messages") or [])
        messages.append(f"[text] Failed: {exc}")
        return {
            "current_step": 1,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "transcript": None,
            "source_metadata": None,
            "source_dir": None,
        }

    # Script path: source detected + video/script loaded + transcript extracted
    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=2,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 2,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_script(state: WorkflowState) -> str:
    """Continue from scenes (step 3) or stop after script ingest."""
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "script_failed"
    return "continue"


def _make_stub_step_node(step_index: int):
    """Create a stub node for pipeline steps 2..14."""

    label = PIPELINE_STEPS[step_index]
    node_name = f"step_{step_index:02d}_{_slug(label)}"

    def _node(state: WorkflowState) -> dict[str, Any]:
        time.sleep(0.15)
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=step_index,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"Completed: {label}")

        update: dict[str, Any] = {
            "current_step": step_index,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.RUNNING.value,
            "error": None,
        }

        if step_index == len(PIPELINE_STEPS) - 1:
            job = state.get("job") or {}
            project = state.get("project") or {}
            update["status"] = JobStatus.COMPLETED.value
            update["result"] = {
                "job_id": job.get("job_id"),
                "project_id": project.get("project_id") or job.get("job_id"),
                "source_type": job.get("source_type"),
                "project_dir": state.get("project_dir"),
                "source_dir": state.get("source_dir"),
                "source_metadata": state.get("source_metadata"),
                "transcript": state.get("transcript"),
                "speech_transcript": state.get("speech_transcript"),
                "analysis": state.get("analysis"),
                "scenes": state.get("scenes"),
                "audio_analysis": state.get("audio_analysis"),
                "speakers": state.get("speakers"),
                "moments": state.get("moments"),
                "clips": state.get("clips"),
                "video_type_pack": state.get("video_type_pack"),
                "visual_style_pack": state.get("visual_style_pack"),
                "environment_pack": state.get("environment_pack"),
                "stories": state.get("stories"),
                "scripts": state.get("scripts"),
                "localizations": state.get("localizations"),
                "cultural_adaptation": state.get("cultural_adaptation"),
                "humor_localization": state.get("humor_localization"),
                "broll_pack": state.get("broll_pack"),
                "voice_pack": state.get("voice_pack"),
                "music_pack": state.get("music_pack"),
                "captions_pack": state.get("captions_pack"),
                "reframe_pack": state.get("reframe_pack"),
                "platform_pack": state.get("platform_pack"),
                "export_path": (
                    (state.get("platform_pack") or {}).get("export_path")
                    if isinstance(state.get("platform_pack"), dict)
                    else None
                )
                or None,
                "detail": (
                    "Pipeline finished — platform metadata prepared for export; "
                    "opening platform URLs is not publishing."
                ),
            }
            logger.info(
                "Video workflow completed project_id=%s",
                project.get("project_id") or job.get("job_id"),
            )

        return update

    _node.__name__ = node_name
    return _node


def _route_after_input(state: WorkflowState) -> str:
    """Conditional edge target after the Input Agent."""
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "input_failed"
    next_agent = state.get("next_agent") or ""
    if next_agent in INGEST_NODES:
        return INGEST_NODES[next_agent]
    # Fallback from source_type on project/job
    project = state.get("project") or {}
    source = project.get("source_type") or (state.get("job") or {}).get("source_type")
    if source == SourceType.YOUTUBE.value:
        return "youtube_ingest"
    if source == SourceType.UPLOAD.value:
        return "local_video_ingest"
    if source == SourceType.SCRIPT.value:
        return "script_ingest"
    return "input_failed"


def _input_failed_node(state: WorkflowState) -> dict[str, Any]:
    """Terminal node when Input Agent validation fails."""
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Input validation failed",
    }


def _youtube_failed_node(state: WorkflowState) -> dict[str, Any]:
    """Terminal node when YouTube Agent fails."""
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "YouTube ingest failed",
    }


def _script_failed_node(state: WorkflowState) -> dict[str, Any]:
    """Terminal node when Text Agent fails."""
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Script ingest failed",
    }


def _transcript_extract_node(state: WorkflowState) -> dict[str, Any]:
    """Real Transcript Agent: local Whisper speech-to-text."""
    project_raw = state.get("project") or {}
    project_dir = state.get("project_dir")
    source_metadata = state.get("source_metadata")
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = TranscriptAgent().run(
            project,
            project_dir=project_dir,
            source_metadata=source_metadata,
        )
    except TranscriptAgentError as exc:
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        steps = _mark_steps_completed(steps, completed_through=1)
        if len(steps) > 2:
            steps[2]["status"] = ProgressStepStatus.FAILED.value
        messages = list(state.get("messages") or [])
        messages.append(f"[transcript] Failed: {exc}")
        return {
            "current_step": 2,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "transcript": None,
            "speech_transcript": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=2,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 2,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_transcript(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "transcript_failed"
    return "continue"


def _transcript_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Transcript extraction failed",
    }


def _video_understanding_node(state: WorkflowState) -> dict[str, Any]:
    """Real Video Understanding Agent: scenes + audio analysis."""
    project_raw = state.get("project") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = VideoUnderstandingAgent().run(
            project,
            project_dir=state.get("project_dir"),
            source_metadata=state.get("source_metadata"),
            speech_transcript=state.get("speech_transcript"),
            transcript=state.get("transcript"),
        )
    except VideoUnderstandingError as exc:
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        steps = _mark_steps_completed(steps, completed_through=2)
        if len(steps) > 3:
            steps[3]["status"] = ProgressStepStatus.FAILED.value
        messages = list(state.get("messages") or [])
        messages.append(f"[video_understanding] Failed: {exc}")
        return {
            "current_step": 3,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "analysis": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=4,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 4,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_understanding(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "understanding_failed"
    return "continue"


def _understanding_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Video understanding failed",
    }


def _scene_detection_node(state: WorkflowState) -> dict[str, Any]:
    """Real Scene Detection Agent: write analysis/scenes.json (signals only)."""
    project_raw = state.get("project") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = SceneDetectionAgent().run(
            project,
            project_dir=state.get("project_dir"),
            source_metadata=state.get("source_metadata"),
            analysis=state.get("analysis"),
            speech_transcript=state.get("speech_transcript"),
            transcript=state.get("transcript"),
        )
    except SceneDetectionError as exc:
        steps = [dict(s) for s in state.get("steps", initial_progress_steps())]
        steps = _mark_steps_completed(steps, completed_through=4)
        messages = list(state.get("messages") or [])
        messages.append(f"[scene_detection] Failed: {exc}")
        return {
            "current_step": 4,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "scenes": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=4,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 4,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_scene_detection(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "scene_detection_failed"
    return "continue"


def _scene_detection_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Scene detection failed",
    }


def _audio_analysis_node(state: WorkflowState) -> dict[str, Any]:
    """Real Audio Analysis Agent: write analysis/audio_analysis.json."""
    project_raw = state.get("project") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = AudioAnalysisAgent().run(
            project,
            project_dir=state.get("project_dir"),
            source_metadata=state.get("source_metadata"),
            analysis=state.get("analysis"),
            speech_transcript=state.get("speech_transcript"),
            transcript=state.get("transcript"),
        )
    except AudioAnalysisError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=4,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[audio_analysis] Failed: {exc}")
        return {
            "current_step": 4,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "audio_analysis": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=4,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 4,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_audio_analysis(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "audio_analysis_failed"
    return "continue"


def _audio_analysis_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Audio analysis failed",
    }


def _speaker_analysis_node(state: WorkflowState) -> dict[str, Any]:
    """Real Speaker Analysis Agent: write analysis/speakers.json."""
    project_raw = state.get("project") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = SpeakerAnalysisAgent().run(
            project,
            project_dir=state.get("project_dir"),
            source_metadata=state.get("source_metadata"),
            analysis=state.get("analysis"),
            speech_transcript=state.get("speech_transcript"),
            transcript=state.get("transcript"),
            audio_analysis=state.get("audio_analysis"),
            scenes=state.get("scenes"),
        )
    except SpeakerAnalysisError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=4,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[speaker_analysis] Failed: {exc}")
        return {
            "current_step": 4,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "speakers": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=4,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 4,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_speaker_analysis(state: WorkflowState) -> str:
    return route_after_speaker(state)


def _speaker_analysis_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Speaker analysis failed",
    }


def _moment_detection_node(state: WorkflowState) -> dict[str, Any]:
    """Moment Detection Agent: write analysis/moments.json (step 5)."""
    project_raw = state.get("project") or {}
    job = state.get("job") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = MomentDetectionAgent().run(
            project,
            project_dir=state.get("project_dir"),
            features=job.get("features"),
            transcript=state.get("transcript"),
            speech_transcript=state.get("speech_transcript"),
            scenes=state.get("scenes"),
            audio_analysis=state.get("audio_analysis"),
            speakers=state.get("speakers"),
            analysis=state.get("analysis"),
            funny_moments=state.get("funny_moments"),
            viral_moments=state.get("viral_moments"),
        )
    except MomentDetectionError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=4,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[moment_detection] Failed: {exc}")
        return {
            "current_step": 5,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "moments": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=5,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 5,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_moment_detection(state: WorkflowState) -> str:
    return route_after_moment(state)


def _moment_detection_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Moment detection failed",
    }


def _funny_moment_node(state: WorkflowState) -> dict[str, Any]:
    """Funny Moment Agent: write analysis/funny_moments.json (step 6)."""
    project_raw = state.get("project") or {}
    job = state.get("job") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = FunnyMomentAgent().run(
            project,
            project_dir=state.get("project_dir"),
            features=job.get("features"),
            transcript=state.get("transcript"),
            speech_transcript=state.get("speech_transcript"),
            scenes=state.get("scenes"),
            audio_analysis=state.get("audio_analysis"),
            speakers=state.get("speakers"),
            analysis=state.get("analysis"),
        )
    except FunnyMomentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=5,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[funny_moment] Failed: {exc}")
        return {
            "current_step": 6,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "funny_moments": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=6,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 6,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_funny_moment(state: WorkflowState) -> str:
    return route_after_funny(state)


def _funny_moment_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Funny moment detection failed",
    }


def _skip_funny_node(state: WorkflowState) -> dict[str, Any]:
    """Graph-level skip: write disabled funny pack without Gemini."""
    project_raw = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["funny_moments"] = False
    project = ProjectMetadata.model_validate(project_raw)
    result = FunnyMomentAgent().run(
        project,
        project_dir=state.get("project_dir"),
        features=features,
        transcript=state.get("transcript"),
        speech_transcript=state.get("speech_transcript"),
        scenes=state.get("scenes"),
        audio_analysis=state.get("audio_analysis"),
        speakers=state.get("speakers"),
        analysis=state.get("analysis"),
    )
    messages = list(state.get("messages") or [])
    messages.append("[funny_moment] Skipped (feature off)")
    messages.extend(result.messages)
    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=6,
    )
    return {
        **result.to_state_dict(),
        "current_step": 6,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _viral_moment_node(state: WorkflowState) -> dict[str, Any]:
    """Viral Moment Agent: write analysis/viral_moments.json (step 7)."""
    project_raw = state.get("project") or {}
    job = state.get("job") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = ViralMomentAgent().run(
            project,
            project_dir=state.get("project_dir"),
            features=job.get("features"),
            transcript=state.get("transcript"),
            speech_transcript=state.get("speech_transcript"),
            scenes=state.get("scenes"),
            audio_analysis=state.get("audio_analysis"),
            speakers=state.get("speakers"),
            analysis=state.get("analysis"),
            funny_moments=state.get("funny_moments"),
        )
    except ViralMomentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=6,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[viral_moment] Failed: {exc}")
        return {
            "current_step": 7,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "viral_moments": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=7,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 7,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_viral_moment(state: WorkflowState) -> str:
    return route_after_viral(state)


def _viral_moment_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Viral moment detection failed",
    }


def _skip_viral_node(state: WorkflowState) -> dict[str, Any]:
    project_raw = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["viral_moments"] = False
    project = ProjectMetadata.model_validate(project_raw)
    result = ViralMomentAgent().run(
        project,
        project_dir=state.get("project_dir"),
        features=features,
        transcript=state.get("transcript"),
        speech_transcript=state.get("speech_transcript"),
        scenes=state.get("scenes"),
        audio_analysis=state.get("audio_analysis"),
        speakers=state.get("speakers"),
        analysis=state.get("analysis"),
        funny_moments=state.get("funny_moments"),
    )
    messages = list(state.get("messages") or [])
    messages.append("[viral_moment] Skipped (feature off)")
    messages.extend(result.messages)
    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=7,
    )
    return {
        **result.to_state_dict(),
        "current_step": 7,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }

def _smart_clip_node(state: WorkflowState) -> dict[str, Any]:
    """Smart Clip Agent: write analysis/clips.json (pipeline step 8)."""
    project_raw = state.get("project") or {}
    job = state.get("job") or {}
    try:
        project = ProjectMetadata.model_validate(project_raw)
        result = SmartClipAgent().run(
            project,
            project_dir=state.get("project_dir"),
            features=job.get("features"),
            config=job.get("config"),
            transcript=state.get("transcript"),
            speech_transcript=state.get("speech_transcript"),
            scenes=state.get("scenes"),
            audio_analysis=state.get("audio_analysis"),
            speakers=state.get("speakers"),
            moments=state.get("moments"),
            funny_moments=state.get("funny_moments"),
            viral_moments=state.get("viral_moments"),
            analysis=state.get("analysis"),
        )
    except SmartClipError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=7,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[smart_clip] Failed: {exc}")
        return {
            "current_step": 8,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "clips": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=8,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 8,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_smart_clip(state: WorkflowState) -> str:
    return route_after_smart_clip_research(state)


def _smart_clip_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Smart clip selection failed",
    }


def _research_node(state: WorkflowState) -> dict[str, Any]:
    """Research Agent: Parallel Search grounding (soft-skips without API key)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for research",
            "research": None,
        }
    job = state.get("job") or {}
    try:
        result = ResearchAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            clips=state.get("clips"),
            transcript=state.get("transcript"),
            speech_transcript=state.get("speech_transcript"),
        )
    except ResearchAgentError as exc:
        messages = list(state.get("messages") or [])
        messages.append(f"[research] Failed: {exc}")
        return {
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "research": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_research_node(state: WorkflowState) -> str:
    return route_after_research(state)


def _research_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Research failed",
    }


def _skip_research_node(state: WorkflowState) -> dict[str, Any]:
    project = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["enable_research"] = False
    job = state.get("job") or {}
    result = ResearchAgent().run(
        project,
        project_dir=state.get("project_dir"),
        config=job.get("config"),
        features=features,
        clips=state.get("clips"),
        transcript=state.get("transcript"),
        speech_transcript=state.get("speech_transcript"),
        force_skip=True,
    )
    messages = list(state.get("messages") or [])
    messages.append("[research] Skipped (feature off)")
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _video_type_node(state: WorkflowState) -> dict[str, Any]:
    """Video Type Agent: resolve preset → analysis/video_type.json (under step 9)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for video type resolution",
            "video_type_pack": None,
        }

    job = state.get("job") or {}
    try:
        result = VideoTypeAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
        )
    except VideoTypeAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=10,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[video_type] Failed: {exc}")
        return {
            "current_step": 9,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "video_type_pack": None,
        }

    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_video_type(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "video_type_failed"
    return "continue"


def _video_type_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Video type resolution failed",
    }


def _visual_style_node(state: WorkflowState) -> dict[str, Any]:
    """Visual Style Agent: resolve plan → analysis/visual_style.json (under step 9)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for visual style resolution",
            "visual_style_pack": None,
        }

    job = state.get("job") or {}
    try:
        result = VisualStyleAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
        )
    except VisualStyleAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=10,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[visual_style] Failed: {exc}")
        return {
            "current_step": 9,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "visual_style_pack": None,
        }

    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_visual_style(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "visual_style_failed"
    return "continue"


def _visual_style_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Visual style resolution failed",
    }


def _environment_node(state: WorkflowState) -> dict[str, Any]:
    """Environment Agent: resolve plan → analysis/environment.json (under step 9)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for environment resolution",
            "environment_pack": None,
        }

    job = state.get("job") or {}
    try:
        result = EnvironmentAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
        )
    except EnvironmentAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=10,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[environment] Failed: {exc}")
        return {
            "current_step": 9,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "environment_pack": None,
        }

    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_environment(state: WorkflowState) -> str:
    return route_after_environment(state)


def _environment_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Environment resolution failed",
    }


def _story_node(state: WorkflowState) -> dict[str, Any]:
    """Story Agent: write analysis/stories.json (part of pipeline step 9)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for story generation",
            "stories": None,
        }

    job = state.get("job") or {}
    try:
        result = StoryAgent().run(
            project,
            project_dir=state.get("project_dir"),
            clips=state.get("clips"),
            transcript=state.get("transcript"),
            speech_transcript=state.get("speech_transcript"),
            config=job.get("config"),
            video_type_pack=state.get("video_type_pack"),
            visual_style_pack=state.get("visual_style_pack"),
            environment_pack=state.get("environment_pack"),
        )
    except StoryAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=8,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[story] Failed: {exc}")
        return {
            "current_step": 9,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "stories": None,
        }

    # Step 9 completes after Script Agent; keep story step running visually.
    steps = list(state.get("steps") or initial_progress_steps())
    steps = [dict(s) for s in steps]
    for i, step in enumerate(steps):
        if i <= 8:
            step["status"] = ProgressStepStatus.COMPLETED.value
        elif i == 9:
            step["status"] = ProgressStepStatus.RUNNING.value
        else:
            step["status"] = ProgressStepStatus.PENDING.value
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 8,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_story(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "story_failed"
    return "continue"


def _story_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Story generation failed",
    }


def _script_node(state: WorkflowState) -> dict[str, Any]:
    """Script Agent: write analysis/scripts.json (completes pipeline step 9)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for script generation",
            "scripts": None,
        }

    job = state.get("job") or {}
    try:
        result = ScriptAgent().run(
            project,
            project_dir=state.get("project_dir"),
            clips=state.get("clips"),
            stories=state.get("stories"),
            transcript=state.get("transcript"),
            speech_transcript=state.get("speech_transcript"),
            config=job.get("config"),
            video_type_pack=state.get("video_type_pack"),
            visual_style_pack=state.get("visual_style_pack"),
            environment_pack=state.get("environment_pack"),
        )
    except ScriptAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=8,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[script] Failed: {exc}")
        return {
            "current_step": 9,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "scripts": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=9,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 9,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_script_gen(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "script_gen_failed"
    return "continue"


def _script_gen_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Script generation failed",
    }


def _storyboard_node(state: WorkflowState) -> dict[str, Any]:
    """Storyboard Agent: write analysis/storyboard.json after scripts."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for storyboard",
            "storyboard": None,
        }
    job = state.get("job") or {}
    try:
        result = StoryboardAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            scripts=state.get("scripts"),
            stories=state.get("stories"),
            clips=state.get("clips"),
        )
    except StoryboardAgentError as exc:
        messages = list(state.get("messages") or [])
        messages.append(f"[storyboard] Failed: {exc}")
        return {
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "storyboard": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_storyboard(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "storyboard_failed"
    if state.get("stop_after_storyboard"):
        return "plan_complete"
    return "continue"


def _storyboard_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Storyboard generation failed",
    }


def _mark_localization_running(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updated = [dict(s) for s in steps]
    for i, step in enumerate(updated):
        if i <= 9:
            step["status"] = ProgressStepStatus.COMPLETED.value
        elif i == 10:
            step["status"] = ProgressStepStatus.RUNNING.value
        else:
            step["status"] = ProgressStepStatus.PENDING.value
    return updated


def _country_node(state: WorkflowState) -> dict[str, Any]:
    """Country Agent: resolve country profile (part of step 10)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for country localization",
            "country_profile": None,
        }

    job = state.get("job") or {}
    try:
        result = CountryAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
        )
    except CountryAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=9,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[country] Failed: {exc}")
        return {
            "current_step": 10,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "country_profile": None,
        }

    steps = _mark_localization_running(
        state.get("steps", initial_progress_steps())
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 9,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_country(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "country_failed"
    return "continue"


def _country_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Country localization failed",
    }


def _regional_node(state: WorkflowState) -> dict[str, Any]:
    """Regional Agent: resolve region profile (part of step 10)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for regional localization",
            "region_profile": None,
        }

    job = state.get("job") or {}
    try:
        result = RegionalAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            country_profile=state.get("country_profile"),
        )
    except RegionalAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=9,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[regional] Failed: {exc}")
        return {
            "current_step": 10,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "region_profile": None,
        }

    steps = _mark_localization_running(
        state.get("steps", initial_progress_steps())
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 9,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_regional(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "regional_failed"
    return "language"


def _regional_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Regional localization failed",
    }


def _cultural_node(state: WorkflowState) -> dict[str, Any]:
    """Cultural Adaptation Agent (part of step 10)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for cultural adaptation",
            "cultural_adaptation": None,
        }

    job = state.get("job") or {}
    try:
        result = CulturalAdaptationAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            scripts=state.get("scripts"),
            locale_pack=state.get("locale_pack"),
        )
    except CulturalAdaptationError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=9,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[cultural] Failed: {exc}")
        return {
            "current_step": 10,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "cultural_adaptation": None,
        }

    steps = _mark_localization_running(
        state.get("steps", initial_progress_steps())
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 9,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_cultural(state: WorkflowState) -> str:
    return route_after_cultural(state)


def _cultural_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Cultural adaptation failed",
    }


def _humor_node(state: WorkflowState) -> dict[str, Any]:
    """Humor Localization Agent (part of step 10)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for humor localization",
            "humor_localization": None,
        }

    job = state.get("job") or {}
    try:
        result = HumorLocalizationAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            scripts=state.get("scripts"),
            locale_pack=state.get("locale_pack"),
            cultural_adaptation=state.get("cultural_adaptation"),
        )
    except HumorLocalizationError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=9,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[humor] Failed: {exc}")
        return {
            "current_step": 10,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "humor_localization": None,
        }

    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=10,
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_humor(state: WorkflowState) -> str:
    return route_after_humor(state)


def _humor_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Humor localization failed",
    }


def _language_node(state: WorkflowState) -> dict[str, Any]:
    """Language Agent: write analysis/localizations.json (part of step 10)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for language localization",
            "localizations": None,
        }

    job = state.get("job") or {}
    try:
        result = LanguageAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            scripts=state.get("scripts"),
            country_profile=state.get("country_profile"),
            region_profile=state.get("region_profile"),
            locale_pack=state.get("locale_pack"),
        )
    except LanguageAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=9,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[language] Failed: {exc}")
        return {
            "current_step": 10,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "localizations": None,
        }

    steps = _mark_localization_running(
        state.get("steps", initial_progress_steps())
    )
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 9,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_language(state: WorkflowState) -> str:
    return route_after_language(state)


def _language_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Language localization failed",
    }


def _skip_cultural_node(state: WorkflowState) -> dict[str, Any]:
    project = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["cultural_adaptation"] = False
    job = state.get("job") or {}
    result = CulturalAdaptationAgent().run(
        project,
        project_dir=state.get("project_dir"),
        config=job.get("config"),
        features=features,
        scripts=state.get("scripts"),
        locale_pack=state.get("locale_pack"),
        country_profile=state.get("country_profile"),
        region_profile=state.get("region_profile"),
    )
    messages = list(state.get("messages") or [])
    messages.append("[cultural] Skipped (feature off)")
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _skip_humor_node(state: WorkflowState) -> dict[str, Any]:
    project = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["regional_humor"] = False
    job = dict(state.get("job") or {})
    cfg = dict(job.get("config") or {})
    cfg["humor_adaptation"] = "none"
    job["config"] = cfg
    result = HumorLocalizationAgent().run(
        project,
        project_dir=state.get("project_dir"),
        config=cfg,
        features=features,
        scripts=state.get("scripts"),
        locale_pack=state.get("locale_pack"),
        country_profile=state.get("country_profile"),
        region_profile=state.get("region_profile"),
    )
    messages = list(state.get("messages") or [])
    messages.append("[humor] Skipped (feature off)")
    messages.extend(result.messages)
    steps = _mark_steps_completed(
        state.get("steps", initial_progress_steps()),
        completed_through=10,
    )
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": steps,
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _skip_broll_node(state: WorkflowState) -> dict[str, Any]:
    project = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["b_roll"] = False
    job = state.get("job") or {}
    result = BRollAgent().run(
        project,
        project_dir=state.get("project_dir"),
        config=job.get("config"),
        features=features,
        clips=state.get("clips"),
        scripts=state.get("scripts"),
        environment_pack=state.get("environment_pack"),
    )
    messages = list(state.get("messages") or [])
    messages.append("[b_roll] Skipped (feature off)")
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _skip_voice_node(state: WorkflowState) -> dict[str, Any]:
    project = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["voice"] = False
    job = state.get("job") or {}
    result = VoiceAgent().run(
        project,
        project_dir=state.get("project_dir"),
        config=job.get("config"),
        features=features,
        scripts=state.get("scripts"),
        locale_pack=state.get("locale_pack"),
    )
    messages = list(state.get("messages") or [])
    messages.append("[voice] Skipped (original / feature off)")
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _skip_music_node(state: WorkflowState) -> dict[str, Any]:
    project = state.get("project") or {}
    features = dict((state.get("job") or {}).get("features") or {})
    features["music"] = False
    job = state.get("job") or {}
    result = MusicAgent().run(
        project,
        project_dir=state.get("project_dir"),
        config=job.get("config"),
        features=features,
        scripts=state.get("scripts"),
        voice_pack=state.get("voice_pack"),
    )
    messages = list(state.get("messages") or [])
    messages.append("[music] Skipped (no music / feature off)")
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _step11_running(state: WorkflowState) -> list[dict[str, Any]]:
    """Keep Captions step RUNNING while B-roll/Voice/Music plan."""
    steps = list(state.get("steps") or initial_progress_steps())
    steps = [dict(s) for s in steps]
    for i, step in enumerate(steps):
        if i <= 10:
            step["status"] = ProgressStepStatus.COMPLETED.value
        elif i == 11:
            step["status"] = ProgressStepStatus.RUNNING.value
        else:
            step["status"] = ProgressStepStatus.PENDING.value
    return steps


def _broll_node(state: WorkflowState) -> dict[str, Any]:
    """B-Roll Agent: write analysis/broll_plan.json (under step 11)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for B-roll planning",
            "broll_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = BRollAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            clips=state.get("clips"),
            scripts=state.get("scripts"),
            environment_pack=state.get("environment_pack"),
        )
    except BRollAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=10,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[b_roll] Failed: {exc}")
        return {
            "current_step": 11,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "broll_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_broll(state: WorkflowState) -> str:
    return route_after_broll(state)


def _broll_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "B-roll planning failed",
    }


def _voice_node(state: WorkflowState) -> dict[str, Any]:
    """Voice Agent: write analysis/voice_plan.json (under step 11)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for voice planning",
            "voice_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = VoiceAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            locale_pack=state.get("locale_pack"),
        )
    except VoiceAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=10,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[voice] Failed: {exc}")
        return {
            "current_step": 11,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "voice_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_voice(state: WorkflowState) -> str:
    return route_after_voice(state)


def _voice_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Voice planning failed",
    }


def _music_node(state: WorkflowState) -> dict[str, Any]:
    """Music Agent: write analysis/music_plan.json (under step 11)."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for music planning",
            "music_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = MusicAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
        )
    except MusicAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=10,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[music] Failed: {exc}")
        return {
            "current_step": 11,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "music_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 10,
        "steps": _step11_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_music(state: WorkflowState) -> str:
    return route_after_music(state)


def _music_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Music planning failed",
    }


def _captions_node(state: WorkflowState) -> dict[str, Any]:
    """Caption Agent: timed cues + SRT/VTT/ASS (+ optional burn-in); completes step 11."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for caption generation",
            "captions_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = CaptionAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            speech_transcript=state.get("speech_transcript"),
            transcript=state.get("transcript"),
            localizations=state.get("localizations"),
            locale_pack=state.get("locale_pack"),
            source_metadata=state.get("source_metadata"),
        )
    except CaptionAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=10,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[captions] Failed: {exc}")
        return {
            "current_step": 11,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "captions_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 11,
        "steps": _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=11,
        ),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_captions(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "captions_failed"
    return "continue"


def _captions_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Caption generation failed",
    }


def _reframe_node(state: WorkflowState) -> dict[str, Any]:
    """Smart Reframe Agent: plan first, optional FFmpeg encode; completes step 12."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for smart reframing",
            "reframe_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = ReframeAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            clips=state.get("clips"),
            analysis=state.get("analysis"),
            speakers=state.get("speakers"),
            video_type_pack=state.get("video_type_pack"),
            source_metadata=state.get("source_metadata"),
            speech_transcript=state.get("speech_transcript"),
        )
    except ReframeAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=11,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[smart_reframe] Failed: {exc}")
        return {
            "current_step": 12,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "reframe_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 12,
        "steps": _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=12,
        ),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_reframe(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "reframe_failed"
    return "continue"


def _reframe_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Smart reframing failed",
    }


def _platform_node(state: WorkflowState) -> dict[str, Any]:
    """Platform Agent: optimize export metadata; completes step 13."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for platform optimization",
            "platform_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = PlatformAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            scripts=state.get("scripts"),
            localizations=state.get("localizations"),
            video_type_pack=state.get("video_type_pack"),
            captions_pack=state.get("captions_pack"),
            reframe_pack=state.get("reframe_pack"),
            locale_pack=state.get("locale_pack"),
        )
    except PlatformAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=12,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[platform] Failed: {exc}")
        return {
            "current_step": 13,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "platform_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 13,
        "steps": _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=13,
        ),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_platform(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "platform_failed"
    return "continue"


def _platform_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Platform optimization failed",
    }


def _step14_running(state: WorkflowState) -> list[dict[str, Any]]:
    """Keep Export completed step RUNNING while Render/Quality resolve."""
    steps = list(state.get("steps") or initial_progress_steps())
    steps = [dict(s) for s in steps]
    for i, step in enumerate(steps):
        if i <= 13:
            step["status"] = ProgressStepStatus.COMPLETED.value
        elif i == 14:
            step["status"] = ProgressStepStatus.RUNNING.value
        else:
            step["status"] = ProgressStepStatus.PENDING.value
    return steps


def _render_node(state: WorkflowState) -> dict[str, Any]:
    """Render Agent: compose final.mp4; step 14 stays RUNNING."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for render",
            "render_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = RenderAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            clips=state.get("clips"),
            captions_pack=state.get("captions_pack"),
            reframe_pack=state.get("reframe_pack"),
            voice_pack=state.get("voice_pack"),
            music_pack=state.get("music_pack"),
            platform_pack=state.get("platform_pack"),
            source_metadata=state.get("source_metadata"),
            speech_transcript=state.get("speech_transcript"),
        )
    except RenderAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=13,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[render] Failed: {exc}")
        return {
            "current_step": 14,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "render_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 13,
        "steps": _step14_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_render(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "render_failed"
    return "continue"


def _render_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Render failed",
    }


def _quality_node(state: WorkflowState) -> dict[str, Any]:
    """Quality Agent: validate/correct; may request one re-render."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for quality checks",
            "quality_pack": None,
        }
    job = state.get("job") or {}
    retry_count = int(state.get("quality_retry_count") or 0)
    try:
        result = QualityAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            render_pack=state.get("render_pack"),
            platform_pack=state.get("platform_pack"),
            captions_pack=state.get("captions_pack"),
            quality_retry_count=retry_count,
        )
    except QualityAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=13,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[quality] Failed: {exc}")
        return {
            "current_step": 14,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "quality_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "current_step": 13,
        "steps": _step14_running(state),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_quality(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "quality_failed"
    pack = state.get("quality_pack") or {}
    report = pack.get("report") if isinstance(pack, dict) else None
    if isinstance(report, dict):
        if report.get("rerender_requested") and int(
            state.get("quality_retry_count") or 0
        ) < 1:
            return "retry"
        if report.get("passed") is False and not report.get("skipped"):
            return "quality_failed"
    return "continue"


def _quality_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Quality validation failed",
    }


def _analytics_node(state: WorkflowState) -> dict[str, Any]:
    """Analytics Agent: rollup metrics before export."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for analytics",
            "analytics": None,
        }
    job = state.get("job") or {}
    try:
        result = AnalyticsAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            clips=state.get("clips"),
            stories=state.get("stories"),
            scripts=state.get("scripts"),
            storyboard=state.get("storyboard"),
            research=state.get("research"),
            quality_pack=state.get("quality_pack"),
            render_pack=state.get("render_pack"),
            platform_pack=state.get("platform_pack"),
            locale_pack=state.get("locale_pack"),
            country_profile=state.get("country_profile"),
        )
    except AnalyticsAgentError as exc:
        messages = list(state.get("messages") or [])
        messages.append(f"[analytics] Failed: {exc}")
        return {
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "analytics": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    return {
        **result.to_state_dict(),
        "messages": messages,
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _route_after_analytics(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "analytics_failed"
    return "continue"


def _analytics_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Analytics rollup failed",
    }


def _quality_retry_bump(state: WorkflowState) -> dict[str, Any]:
    """Increment retry count before looping back to render."""
    count = int(state.get("quality_retry_count") or 0) + 1
    messages = list(state.get("messages") or [])
    messages.append(f"[quality] Re-render requested (attempt {count})")
    return {
        "quality_retry_count": count,
        "messages": messages,
        "steps": _step14_running(state),
        "status": JobStatus.RUNNING.value,
        "error": None,
    }


def _export_node(state: WorkflowState) -> dict[str, Any]:
    """Export Agent: package deliverables; completes step 14 and the job."""
    project = state.get("project")
    if not project:
        return {
            "status": JobStatus.FAILED.value,
            "error": "Missing project for export",
            "export_pack": None,
        }
    job = state.get("job") or {}
    try:
        result = ExportAgent().run(
            project,
            project_dir=state.get("project_dir"),
            config=job.get("config"),
            features=job.get("features"),
            render_pack=state.get("render_pack"),
            quality_pack=state.get("quality_pack"),
            captions_pack=state.get("captions_pack"),
            platform_pack=state.get("platform_pack"),
            workflow_state=dict(state),
        )
    except ExportAgentError as exc:
        steps = _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=13,
        )
        messages = list(state.get("messages") or [])
        messages.append(f"[export] Failed: {exc}")
        return {
            "current_step": 14,
            "steps": steps,
            "messages": messages,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "export_pack": None,
        }
    messages = list(state.get("messages") or [])
    messages.extend(result.messages)
    export_path = result.export_pack.export_path
    merged = dict(state)
    merged.update(result.to_state_dict())
    merged["status"] = JobStatus.COMPLETED.value
    merged["error"] = None
    flat = project_state_view(merged)
    project = state.get("project") or {}
    result_payload = {
        "job_id": job.get("job_id"),
        "project_id": project.get("project_id") or job.get("job_id"),
        "source_type": job.get("source_type"),
        "project_dir": state.get("project_dir"),
        "source_dir": state.get("source_dir"),
        "source_metadata": state.get("source_metadata"),
        "transcript": state.get("transcript"),
        "speech_transcript": state.get("speech_transcript"),
        "analysis": state.get("analysis"),
        "scenes": state.get("scenes"),
        "audio_analysis": state.get("audio_analysis"),
        "speakers": state.get("speakers"),
        "moments": state.get("moments"),
        "clips": state.get("clips"),
        "video_type_pack": state.get("video_type_pack"),
        "visual_style_pack": state.get("visual_style_pack"),
        "environment_pack": state.get("environment_pack"),
        "stories": state.get("stories"),
        "scripts": state.get("scripts"),
        "localizations": state.get("localizations"),
        "cultural_adaptation": state.get("cultural_adaptation"),
        "humor_localization": state.get("humor_localization"),
        "broll_pack": state.get("broll_pack"),
        "voice_pack": state.get("voice_pack"),
        "music_pack": state.get("music_pack"),
        "captions_pack": state.get("captions_pack"),
        "reframe_pack": state.get("reframe_pack"),
        "platform_pack": state.get("platform_pack"),
        "render_pack": state.get("render_pack"),
        "quality_pack": state.get("quality_pack"),
        "export_pack": result.export_pack.model_dump(mode="json"),
        "export_path": export_path,
        "output_files": flat.get("output_files") or {},
        "detail": (
            "Pipeline finished — export package ready; "
            "opening platform URLs is not publishing."
        ),
        **{k: flat[k] for k in (
            "duration",
            "video_path",
            "selected_clips",
            "story",
            "script",
            "country",
            "region",
            "language",
            "cultural_context",
            "humor_context",
            "render_plan",
            "quality_report",
            "errors",
            "progress",
        ) if k in flat},
    }
    return {
        **result.to_state_dict(),
        "current_step": 14,
        "steps": _mark_steps_completed(
            state.get("steps", initial_progress_steps()),
            completed_through=14,
        ),
        "messages": messages,
        "status": JobStatus.COMPLETED.value,
        "error": None,
        "result": result_payload,
    }


def _route_after_export(state: WorkflowState) -> str:
    if state.get("status") == JobStatus.FAILED.value or state.get("error"):
        return "export_failed"
    return "continue"


def _export_failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": JobStatus.FAILED.value,
        "error": state.get("error") or "Export packaging failed",
    }


def build_video_graph():
    """Build graph: supervisor → … → research → story → … → storyboard → … → analytics → export."""
    graph = StateGraph(WorkflowState)

    graph.add_node(SUPERVISOR_NODE, _supervisor_node)
    graph.add_node("supervisor_failed", _supervisor_failed_node)
    graph.add_node("input_agent", _input_agent_node)
    graph.add_node("input_failed", _input_failed_node)
    graph.add_node("youtube_ingest", _youtube_ingest_node)
    graph.add_node("youtube_failed", _youtube_failed_node)
    graph.add_node("local_video_ingest", _local_video_ingest_node)
    graph.add_node("local_video_failed", _local_video_failed_node)
    graph.add_node("script_ingest", _script_ingest_node)
    graph.add_node("script_failed", _script_failed_node)
    graph.add_node(TRANSCRIPT_NODE, _transcript_extract_node)
    graph.add_node("transcript_failed", _transcript_failed_node)
    graph.add_node(UNDERSTANDING_NODE, _video_understanding_node)
    graph.add_node("understanding_failed", _understanding_failed_node)
    graph.add_node(SCENE_DETECTION_NODE, _scene_detection_node)
    graph.add_node("scene_detection_failed", _scene_detection_failed_node)
    graph.add_node(AUDIO_ANALYSIS_NODE, _audio_analysis_node)
    graph.add_node("audio_analysis_failed", _audio_analysis_failed_node)
    graph.add_node(SPEAKER_ANALYSIS_NODE, _speaker_analysis_node)
    graph.add_node("speaker_analysis_failed", _speaker_analysis_failed_node)
    graph.add_node(FUNNY_MOMENT_NODE, _funny_moment_node)
    graph.add_node("funny_moment_failed", _funny_moment_failed_node)
    graph.add_node(VIRAL_MOMENT_NODE, _viral_moment_node)
    graph.add_node("viral_moment_failed", _viral_moment_failed_node)
    graph.add_node(MOMENT_DETECTION_NODE, _moment_detection_node)
    graph.add_node("moment_detection_failed", _moment_detection_failed_node)
    graph.add_node(SMART_CLIP_NODE, _smart_clip_node)
    graph.add_node("smart_clip_failed", _smart_clip_failed_node)
    graph.add_node(RESEARCH_NODE, _research_node)
    graph.add_node("research_failed", _research_failed_node)
    graph.add_node("skip_research", _skip_research_node)
    graph.add_node(VIDEO_TYPE_NODE, _video_type_node)
    graph.add_node("video_type_failed", _video_type_failed_node)
    graph.add_node(VISUAL_STYLE_NODE, _visual_style_node)
    graph.add_node("visual_style_failed", _visual_style_failed_node)
    graph.add_node(ENVIRONMENT_NODE, _environment_node)
    graph.add_node("environment_failed", _environment_failed_node)
    graph.add_node(STORY_NODE, _story_node)
    graph.add_node("story_failed", _story_failed_node)
    graph.add_node(SCRIPT_NODE, _script_node)
    graph.add_node("script_gen_failed", _script_gen_failed_node)
    graph.add_node(STORYBOARD_NODE, _storyboard_node)
    graph.add_node("storyboard_failed", _storyboard_failed_node)
    graph.add_node(COUNTRY_NODE, _country_node)
    graph.add_node("country_failed", _country_failed_node)
    graph.add_node(REGIONAL_NODE, _regional_node)
    graph.add_node("regional_failed", _regional_failed_node)
    graph.add_node(CULTURAL_NODE, _cultural_node)
    graph.add_node("cultural_failed", _cultural_failed_node)
    graph.add_node(HUMOR_NODE, _humor_node)
    graph.add_node("humor_failed", _humor_failed_node)
    graph.add_node(LANGUAGE_NODE, _language_node)
    graph.add_node("language_failed", _language_failed_node)
    graph.add_node(BROLL_NODE, _broll_node)
    graph.add_node("b_roll_failed", _broll_failed_node)
    graph.add_node(VOICE_NODE, _voice_node)
    graph.add_node("voice_failed", _voice_failed_node)
    graph.add_node(MUSIC_NODE, _music_node)
    graph.add_node("music_failed", _music_failed_node)
    graph.add_node(CAPTIONS_NODE, _captions_node)
    graph.add_node("captions_failed", _captions_failed_node)
    graph.add_node(REFRAME_NODE, _reframe_node)
    graph.add_node("reframe_failed", _reframe_failed_node)
    graph.add_node(PLATFORM_NODE, _platform_node)
    graph.add_node("platform_failed", _platform_failed_node)
    graph.add_node(RENDER_NODE, _render_node)
    graph.add_node("render_failed", _render_failed_node)
    graph.add_node(QUALITY_NODE, _quality_node)
    graph.add_node("quality_failed", _quality_failed_node)
    graph.add_node("quality_retry", _quality_retry_bump)
    graph.add_node(ANALYTICS_NODE, _analytics_node)
    graph.add_node("analytics_failed", _analytics_failed_node)
    graph.add_node(EXPORT_NODE, _export_node)
    graph.add_node("export_failed", _export_failed_node)
    graph.add_node("skip_funny", _skip_funny_node)
    graph.add_node("skip_viral", _skip_viral_node)
    graph.add_node("skip_cultural", _skip_cultural_node)
    graph.add_node("skip_humor", _skip_humor_node)
    graph.add_node("skip_broll", _skip_broll_node)
    graph.add_node("skip_voice", _skip_voice_node)
    graph.add_node("skip_music", _skip_music_node)

    graph.add_edge(START, SUPERVISOR_NODE)
    graph.add_conditional_edges(
        SUPERVISOR_NODE,
        _route_after_supervisor,
        {
            "continue": "input_agent",
            "supervisor_failed": "supervisor_failed",
        },
    )
    graph.add_conditional_edges(
        "input_agent",
        _route_after_input,
        {
            "youtube_ingest": "youtube_ingest",
            "local_video_ingest": "local_video_ingest",
            "script_ingest": "script_ingest",
            "input_failed": "input_failed",
        },
    )
    graph.add_edge("supervisor_failed", END)
    graph.add_edge("input_failed", END)
    graph.add_edge("youtube_failed", END)
    graph.add_edge("script_failed", END)
    graph.add_edge("transcript_failed", END)
    graph.add_edge("understanding_failed", END)
    graph.add_edge("scene_detection_failed", END)
    graph.add_edge("audio_analysis_failed", END)
    graph.add_edge("speaker_analysis_failed", END)
    graph.add_edge("funny_moment_failed", END)
    graph.add_edge("viral_moment_failed", END)
    graph.add_edge("moment_detection_failed", END)
    graph.add_edge("smart_clip_failed", END)
    graph.add_edge("research_failed", END)
    graph.add_edge("video_type_failed", END)
    graph.add_edge("visual_style_failed", END)
    graph.add_edge("environment_failed", END)
    graph.add_edge("story_failed", END)
    graph.add_edge("script_gen_failed", END)
    graph.add_edge("storyboard_failed", END)
    graph.add_edge("country_failed", END)
    graph.add_edge("regional_failed", END)
    graph.add_edge("cultural_failed", END)
    graph.add_edge("humor_failed", END)
    graph.add_edge("language_failed", END)
    graph.add_edge("b_roll_failed", END)
    graph.add_edge("voice_failed", END)
    graph.add_edge("music_failed", END)
    graph.add_edge("captions_failed", END)
    graph.add_edge("reframe_failed", END)
    graph.add_edge("platform_failed", END)
    graph.add_edge("render_failed", END)
    graph.add_edge("quality_failed", END)
    graph.add_edge("analytics_failed", END)
    graph.add_edge("export_failed", END)

    graph.add_conditional_edges(
        "youtube_ingest",
        _route_after_youtube,
        {
            "continue": TRANSCRIPT_NODE,
            "youtube_failed": "youtube_failed",
        },
    )
    graph.add_conditional_edges(
        "local_video_ingest",
        _route_after_local_video,
        {
            "continue": TRANSCRIPT_NODE,
            "local_video_failed": "local_video_failed",
        },
    )
    graph.add_edge("local_video_failed", END)
    graph.add_conditional_edges(
        TRANSCRIPT_NODE,
        _route_after_transcript,
        {
            "continue": UNDERSTANDING_NODE,
            "transcript_failed": "transcript_failed",
        },
    )
    graph.add_conditional_edges(
        "script_ingest",
        _route_after_script,
        {
            "continue": UNDERSTANDING_NODE,
            "script_failed": "script_failed",
        },
    )
    graph.add_conditional_edges(
        UNDERSTANDING_NODE,
        _route_after_understanding,
        {
            "continue": SCENE_DETECTION_NODE,
            "understanding_failed": "understanding_failed",
        },
    )
    graph.add_conditional_edges(
        SCENE_DETECTION_NODE,
        _route_after_scene_detection,
        {
            "continue": AUDIO_ANALYSIS_NODE,
            "scene_detection_failed": "scene_detection_failed",
        },
    )
    graph.add_conditional_edges(
        AUDIO_ANALYSIS_NODE,
        _route_after_audio_analysis,
        {
            "continue": SPEAKER_ANALYSIS_NODE,
            "audio_analysis_failed": "audio_analysis_failed",
        },
    )
    graph.add_conditional_edges(
        SPEAKER_ANALYSIS_NODE,
        _route_after_speaker_analysis,
        {
            "continue": MOMENT_DETECTION_NODE,
            "speaker_analysis_failed": "speaker_analysis_failed",
        },
    )
    graph.add_conditional_edges(
        MOMENT_DETECTION_NODE,
        _route_after_moment_detection,
        {
            "funny": FUNNY_MOMENT_NODE,
            "skip_funny": "skip_funny",
            "moment_detection_failed": "moment_detection_failed",
        },
    )
    graph.add_conditional_edges(
        FUNNY_MOMENT_NODE,
        _route_after_funny_moment,
        {
            "viral": VIRAL_MOMENT_NODE,
            "skip_viral": "skip_viral",
            "funny_moment_failed": "funny_moment_failed",
        },
    )
    graph.add_conditional_edges(
        "skip_funny",
        _route_after_funny_moment,
        {
            "viral": VIRAL_MOMENT_NODE,
            "skip_viral": "skip_viral",
            "funny_moment_failed": "funny_moment_failed",
        },
    )
    graph.add_conditional_edges(
        VIRAL_MOMENT_NODE,
        _route_after_viral_moment,
        {
            "continue": SMART_CLIP_NODE,
            "viral_moment_failed": "viral_moment_failed",
        },
    )
    graph.add_edge("skip_viral", SMART_CLIP_NODE)
    graph.add_conditional_edges(
        SMART_CLIP_NODE,
        _route_after_smart_clip,
        {
            "research": RESEARCH_NODE,
            "skip_research": "skip_research",
            "smart_clip_failed": "smart_clip_failed",
        },
    )
    graph.add_conditional_edges(
        RESEARCH_NODE,
        _route_after_research_node,
        {
            "continue": STORY_NODE,
            "research_failed": "research_failed",
        },
    )
    graph.add_edge("skip_research", STORY_NODE)
    graph.add_conditional_edges(
        STORY_NODE,
        _route_after_story,
        {
            "continue": SCRIPT_NODE,
            "story_failed": "story_failed",
        },
    )
    graph.add_conditional_edges(
        SCRIPT_NODE,
        _route_after_script_gen,
        {
            "continue": STORYBOARD_NODE,
            "script_gen_failed": "script_gen_failed",
        },
    )
    graph.add_conditional_edges(
        STORYBOARD_NODE,
        _route_after_storyboard,
        {
            "continue": COUNTRY_NODE,
            "storyboard_failed": "storyboard_failed",
            "plan_complete": END,
        },
    )
    graph.add_conditional_edges(
        COUNTRY_NODE,
        _route_after_country,
        {
            "continue": REGIONAL_NODE,
            "country_failed": "country_failed",
        },
    )
    graph.add_conditional_edges(
        REGIONAL_NODE,
        _route_after_regional,
        {
            "language": LANGUAGE_NODE,
            "regional_failed": "regional_failed",
        },
    )
    graph.add_conditional_edges(
        LANGUAGE_NODE,
        _route_after_language,
        {
            "cultural": CULTURAL_NODE,
            "skip_cultural": "skip_cultural",
            "language_failed": "language_failed",
        },
    )
    graph.add_conditional_edges(
        CULTURAL_NODE,
        _route_after_cultural,
        {
            "humor": HUMOR_NODE,
            "skip_humor": "skip_humor",
            "cultural_failed": "cultural_failed",
        },
    )
    graph.add_conditional_edges(
        "skip_cultural",
        _route_after_cultural,
        {
            "humor": HUMOR_NODE,
            "skip_humor": "skip_humor",
            "cultural_failed": "cultural_failed",
        },
    )
    graph.add_conditional_edges(
        HUMOR_NODE,
        _route_after_humor,
        {
            "continue": VIDEO_TYPE_NODE,
            "humor_failed": "humor_failed",
        },
    )
    graph.add_edge("skip_humor", VIDEO_TYPE_NODE)
    graph.add_conditional_edges(
        VIDEO_TYPE_NODE,
        _route_after_video_type,
        {
            "continue": VISUAL_STYLE_NODE,
            "video_type_failed": "video_type_failed",
        },
    )
    graph.add_conditional_edges(
        VISUAL_STYLE_NODE,
        _route_after_visual_style,
        {
            "continue": ENVIRONMENT_NODE,
            "visual_style_failed": "visual_style_failed",
        },
    )
    graph.add_conditional_edges(
        ENVIRONMENT_NODE,
        _route_after_environment,
        {
            "b_roll": BROLL_NODE,
            "skip_broll": "skip_broll",
            "environment_failed": "environment_failed",
        },
    )
    graph.add_conditional_edges(
        BROLL_NODE,
        _route_after_broll,
        {
            "voice": VOICE_NODE,
            "skip_voice": "skip_voice",
            "b_roll_failed": "b_roll_failed",
        },
    )
    graph.add_conditional_edges(
        "skip_broll",
        _route_after_broll,
        {
            "voice": VOICE_NODE,
            "skip_voice": "skip_voice",
            "b_roll_failed": "b_roll_failed",
        },
    )
    graph.add_conditional_edges(
        VOICE_NODE,
        _route_after_voice,
        {
            "music": MUSIC_NODE,
            "skip_music": "skip_music",
            "voice_failed": "voice_failed",
        },
    )
    graph.add_conditional_edges(
        "skip_voice",
        _route_after_voice,
        {
            "music": MUSIC_NODE,
            "skip_music": "skip_music",
            "voice_failed": "voice_failed",
        },
    )
    graph.add_conditional_edges(
        MUSIC_NODE,
        _route_after_music,
        {
            "continue": CAPTIONS_NODE,
            "music_failed": "music_failed",
        },
    )
    graph.add_edge("skip_music", CAPTIONS_NODE)
    graph.add_conditional_edges(
        CAPTIONS_NODE,
        _route_after_captions,
        {
            "continue": REFRAME_NODE,
            "captions_failed": "captions_failed",
        },
    )
    graph.add_conditional_edges(
        REFRAME_NODE,
        _route_after_reframe,
        {
            "continue": PLATFORM_NODE,
            "reframe_failed": "reframe_failed",
        },
    )
    graph.add_conditional_edges(
        PLATFORM_NODE,
        _route_after_platform,
        {
            "continue": RENDER_NODE,
            "platform_failed": "platform_failed",
        },
    )
    graph.add_conditional_edges(
        RENDER_NODE,
        _route_after_render,
        {
            "continue": QUALITY_NODE,
            "render_failed": "render_failed",
        },
    )
    graph.add_conditional_edges(
        QUALITY_NODE,
        _route_after_quality,
        {
            "continue": ANALYTICS_NODE,
            "retry": "quality_retry",
            "quality_failed": "quality_failed",
        },
    )
    graph.add_edge("quality_retry", RENDER_NODE)
    graph.add_conditional_edges(
        ANALYTICS_NODE,
        _route_after_analytics,
        {
            "continue": EXPORT_NODE,
            "analytics_failed": "analytics_failed",
        },
    )
    graph.add_conditional_edges(
        EXPORT_NODE,
        _route_after_export,
        {
            "continue": END,
            "export_failed": "export_failed",
        },
    )

    return graph.compile()


def build_graph():
    """Alias used by tests and package exports."""
    return build_video_graph()


def _initial_state(request: VideoJobRequest) -> WorkflowState:
    return {
        "job": request.model_dump(mode="json"),
        "status": JobStatus.RUNNING.value,
        "current_step": -1,
        "steps": initial_progress_steps(),
        "messages": [],
        "error": None,
        "result": None,
        "project": None,
        "project_dir": None,
        "next_agent": None,
        "source_metadata": None,
        "source_dir": None,
        "transcript": None,
        "speech_transcript": None,
        "analysis": None,
        "scenes": None,
        "audio_analysis": None,
        "speakers": None,
        "funny_moments": None,
        "viral_moments": None,
        "moments": None,
        "clips": None,
        "research": None,
        "supervisor": None,
        "storyboard": None,
        "analytics": None,
        "video_type_pack": None,
        "visual_style_pack": None,
        "environment_pack": None,
        "stories": None,
        "scripts": None,
        "country_profile": None,
        "region_profile": None,
        "locale_pack": None,
        "cultural_adaptation": None,
        "humor_localization": None,
        "localizations": None,
        "broll_pack": None,
        "voice_pack": None,
        "music_pack": None,
        "captions_pack": None,
        "reframe_pack": None,
        "platform_pack": None,
        "render_pack": None,
        "quality_pack": None,
        "export_pack": None,
        "quality_retry_count": 0,
        "stop_after_storyboard": False,
    }


def run_video_workflow(
    request: VideoJobRequest,
    on_step: OnStepCallback | None = None,
) -> dict[str, Any]:
    """Run the full pipeline, optionally notifying after each streamed update."""
    try:
        compiled = build_video_graph()
        state: dict[str, Any] = dict(_initial_state(request))
        state = _stream_workflow(compiled, state, on_step=on_step)
        return state
    except WorkflowError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Video workflow failed")
        raise WorkflowError(f"Workflow failed: {exc}") from exc


def _stream_workflow(
    compiled: Any,
    state: dict[str, Any],
    on_step: OnStepCallback | None = None,
) -> dict[str, Any]:
    if on_step is not None:
        on_step(dict(state))
    for event in compiled.stream(state, stream_mode="values"):
        state = dict(event)
        steps = [dict(s) for s in state.get("steps", [])]
        current = state.get("current_step", -1)
        next_idx = current + 1
        if (
            state.get("status") == JobStatus.RUNNING.value
            and 0 <= next_idx < len(steps)
            and steps[next_idx].get("status") == ProgressStepStatus.PENDING.value
        ):
            steps[next_idx]["status"] = ProgressStepStatus.RUNNING.value
            state["steps"] = steps
        if on_step is not None:
            on_step(dict(state))
    if state.get("status") == JobStatus.FAILED.value:
        raise WorkflowError(state.get("error") or "Workflow failed")
    return state


def build_produce_phase_graph():
    """Resume graph: START → country → … → analytics → export → END."""
    graph = StateGraph(WorkflowState)
    graph.add_node(COUNTRY_NODE, _country_node)
    graph.add_node("country_failed", _country_failed_node)
    graph.add_node(REGIONAL_NODE, _regional_node)
    graph.add_node("regional_failed", _regional_failed_node)
    graph.add_node(CULTURAL_NODE, _cultural_node)
    graph.add_node("cultural_failed", _cultural_failed_node)
    graph.add_node(HUMOR_NODE, _humor_node)
    graph.add_node("humor_failed", _humor_failed_node)
    graph.add_node(LANGUAGE_NODE, _language_node)
    graph.add_node("language_failed", _language_failed_node)
    graph.add_node(VIDEO_TYPE_NODE, _video_type_node)
    graph.add_node("video_type_failed", _video_type_failed_node)
    graph.add_node(VISUAL_STYLE_NODE, _visual_style_node)
    graph.add_node("visual_style_failed", _visual_style_failed_node)
    graph.add_node(ENVIRONMENT_NODE, _environment_node)
    graph.add_node("environment_failed", _environment_failed_node)
    graph.add_node(BROLL_NODE, _broll_node)
    graph.add_node("b_roll_failed", _broll_failed_node)
    graph.add_node(VOICE_NODE, _voice_node)
    graph.add_node("voice_failed", _voice_failed_node)
    graph.add_node(MUSIC_NODE, _music_node)
    graph.add_node("music_failed", _music_failed_node)
    graph.add_node(CAPTIONS_NODE, _captions_node)
    graph.add_node("captions_failed", _captions_failed_node)
    graph.add_node(REFRAME_NODE, _reframe_node)
    graph.add_node("reframe_failed", _reframe_failed_node)
    graph.add_node(PLATFORM_NODE, _platform_node)
    graph.add_node("platform_failed", _platform_failed_node)
    graph.add_node(RENDER_NODE, _render_node)
    graph.add_node("render_failed", _render_failed_node)
    graph.add_node(QUALITY_NODE, _quality_node)
    graph.add_node("quality_failed", _quality_failed_node)
    graph.add_node("quality_retry", _quality_retry_bump)
    graph.add_node(ANALYTICS_NODE, _analytics_node)
    graph.add_node("analytics_failed", _analytics_failed_node)
    graph.add_node(EXPORT_NODE, _export_node)
    graph.add_node("export_failed", _export_failed_node)
    graph.add_node("skip_cultural", _skip_cultural_node)
    graph.add_node("skip_humor", _skip_humor_node)
    graph.add_node("skip_broll", _skip_broll_node)
    graph.add_node("skip_voice", _skip_voice_node)
    graph.add_node("skip_music", _skip_music_node)

    for failed in (
        "country_failed",
        "regional_failed",
        "cultural_failed",
        "humor_failed",
        "language_failed",
        "video_type_failed",
        "visual_style_failed",
        "environment_failed",
        "b_roll_failed",
        "voice_failed",
        "music_failed",
        "captions_failed",
        "reframe_failed",
        "platform_failed",
        "render_failed",
        "quality_failed",
        "analytics_failed",
        "export_failed",
    ):
        graph.add_edge(failed, END)

    graph.add_edge(START, COUNTRY_NODE)
    graph.add_conditional_edges(
        COUNTRY_NODE,
        _route_after_country,
        {"continue": REGIONAL_NODE, "country_failed": "country_failed"},
    )
    graph.add_conditional_edges(
        REGIONAL_NODE,
        _route_after_regional,
        {"language": LANGUAGE_NODE, "regional_failed": "regional_failed"},
    )
    graph.add_conditional_edges(
        LANGUAGE_NODE,
        _route_after_language,
        {
            "cultural": CULTURAL_NODE,
            "skip_cultural": "skip_cultural",
            "language_failed": "language_failed",
        },
    )
    graph.add_conditional_edges(
        CULTURAL_NODE,
        _route_after_cultural,
        {
            "humor": HUMOR_NODE,
            "skip_humor": "skip_humor",
            "cultural_failed": "cultural_failed",
        },
    )
    graph.add_conditional_edges(
        "skip_cultural",
        _route_after_cultural,
        {
            "humor": HUMOR_NODE,
            "skip_humor": "skip_humor",
            "cultural_failed": "cultural_failed",
        },
    )
    graph.add_conditional_edges(
        HUMOR_NODE,
        _route_after_humor,
        {"continue": VIDEO_TYPE_NODE, "humor_failed": "humor_failed"},
    )
    graph.add_edge("skip_humor", VIDEO_TYPE_NODE)
    graph.add_conditional_edges(
        VIDEO_TYPE_NODE,
        _route_after_video_type,
        {"continue": VISUAL_STYLE_NODE, "video_type_failed": "video_type_failed"},
    )
    graph.add_conditional_edges(
        VISUAL_STYLE_NODE,
        _route_after_visual_style,
        {"continue": ENVIRONMENT_NODE, "visual_style_failed": "visual_style_failed"},
    )
    graph.add_conditional_edges(
        ENVIRONMENT_NODE,
        _route_after_environment,
        {
            "b_roll": BROLL_NODE,
            "skip_broll": "skip_broll",
            "environment_failed": "environment_failed",
        },
    )
    graph.add_conditional_edges(
        BROLL_NODE,
        _route_after_broll,
        {
            "voice": VOICE_NODE,
            "skip_voice": "skip_voice",
            "b_roll_failed": "b_roll_failed",
        },
    )
    graph.add_conditional_edges(
        "skip_broll",
        _route_after_broll,
        {
            "voice": VOICE_NODE,
            "skip_voice": "skip_voice",
            "b_roll_failed": "b_roll_failed",
        },
    )
    graph.add_conditional_edges(
        VOICE_NODE,
        _route_after_voice,
        {
            "music": MUSIC_NODE,
            "skip_music": "skip_music",
            "voice_failed": "voice_failed",
        },
    )
    graph.add_conditional_edges(
        "skip_voice",
        _route_after_voice,
        {
            "music": MUSIC_NODE,
            "skip_music": "skip_music",
            "voice_failed": "voice_failed",
        },
    )
    graph.add_conditional_edges(
        MUSIC_NODE,
        _route_after_music,
        {"continue": CAPTIONS_NODE, "music_failed": "music_failed"},
    )
    graph.add_edge("skip_music", CAPTIONS_NODE)
    graph.add_conditional_edges(
        CAPTIONS_NODE,
        _route_after_captions,
        {"continue": REFRAME_NODE, "captions_failed": "captions_failed"},
    )
    graph.add_conditional_edges(
        REFRAME_NODE,
        _route_after_reframe,
        {"continue": PLATFORM_NODE, "reframe_failed": "reframe_failed"},
    )
    graph.add_conditional_edges(
        PLATFORM_NODE,
        _route_after_platform,
        {"continue": RENDER_NODE, "platform_failed": "platform_failed"},
    )
    graph.add_conditional_edges(
        RENDER_NODE,
        _route_after_render,
        {"continue": QUALITY_NODE, "render_failed": "render_failed"},
    )
    graph.add_conditional_edges(
        QUALITY_NODE,
        _route_after_quality,
        {
            "continue": ANALYTICS_NODE,
            "retry": "quality_retry",
            "quality_failed": "quality_failed",
        },
    )
    graph.add_edge("quality_retry", RENDER_NODE)
    graph.add_conditional_edges(
        ANALYTICS_NODE,
        _route_after_analytics,
        {"continue": EXPORT_NODE, "analytics_failed": "analytics_failed"},
    )
    graph.add_conditional_edges(
        EXPORT_NODE,
        _route_after_export,
        {"continue": END, "export_failed": "export_failed"},
    )
    return graph.compile()


def run_video_workflow_until_plan(
    request: VideoJobRequest,
    on_step: OnStepCallback | None = None,
) -> dict[str, Any]:
    """Phase A: run through storyboard, then stop for human plan approval."""
    try:
        compiled = build_video_graph()
        state: dict[str, Any] = dict(_initial_state(request))
        state["stop_after_storyboard"] = True
        state = _stream_workflow(compiled, state, on_step=on_step)
        if state.get("status") == JobStatus.RUNNING.value:
            state["status"] = JobStatus.COMPLETED.value
            state["result"] = project_state_view(state)
        return state
    except WorkflowError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Plan-phase workflow failed")
        raise WorkflowError(f"Plan phase failed: {exc}") from exc


def run_video_workflow_from_plan(
    checkpoint: dict[str, Any],
    on_step: OnStepCallback | None = None,
) -> dict[str, Any]:
    """Phase B: resume from plan checkpoint through produce → export."""
    try:
        compiled = build_produce_phase_graph()
        state = dict(checkpoint)
        state["stop_after_storyboard"] = False
        state["status"] = JobStatus.RUNNING.value
        state["error"] = None
        state = _stream_workflow(compiled, state, on_step=on_step)
        if state.get("status") == JobStatus.RUNNING.value:
            state["status"] = JobStatus.COMPLETED.value
            state["result"] = project_state_view(state)
        return state
    except WorkflowError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Produce-phase workflow failed")
        raise WorkflowError(f"Produce phase failed: {exc}") from exc


def run_workflow(user_input: str) -> dict[str, Any]:
    """Compat wrapper: treat free text as a script-source job."""
    request = VideoJobRequest(
        source_type=SourceType.SCRIPT,
        script_text=user_input or "placeholder",
        config=VideoJobConfig(),
    )
    return run_video_workflow(request)
