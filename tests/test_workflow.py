"""Tests for the LangGraph video generation workflow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from agents.audio_analysis_agent import AudioAnalysisAgent
from agents.funny_moment_agent import FunnyMomentAgent
from agents.language_agent import LanguageAgent
from agents.moment_detection_agent import MomentDetectionAgent
from agents.scene_detection_agent import SceneDetectionAgent
from agents.script_agent import ScriptAgent
from agents.smart_clip_agent import SmartClipAgent
from agents.speaker_analysis_agent import SpeakerAnalysisAgent
from agents.story_agent import StoryAgent
from agents.text_agent import TextAgent
from agents.transcript_agent import TranscriptAgent
from agents.video_understanding_agent import VideoUnderstandingAgent
from agents.viral_moment_agent import ViralMomentAgent
from config.settings import get_settings
from graph.workflow import (
    AUDIO_ANALYSIS_NODE,
    BROLL_NODE,
    CAPTIONS_NODE,
    COUNTRY_NODE,
    CULTURAL_NODE,
    ENVIRONMENT_NODE,
    EXPORT_NODE,
    FUNNY_MOMENT_NODE,
    HUMOR_NODE,
    LANGUAGE_NODE,
    MOMENT_DETECTION_NODE,
    MUSIC_NODE,
    PLATFORM_NODE,
    QUALITY_NODE,
    REFRAME_NODE,
    REGIONAL_NODE,
    RENDER_NODE,
    SCENE_DETECTION_NODE,
    SCRIPT_NODE,
    SMART_CLIP_NODE,
    SPEAKER_ANALYSIS_NODE,
    STEP_NODE_NAMES,
    STORY_NODE,
    TRANSCRIPT_NODE,
    UNDERSTANDING_NODE,
    VIDEO_TYPE_NODE,
    VISUAL_STYLE_NODE,
    VIRAL_MOMENT_NODE,
    VOICE_NODE,
    build_graph,
    build_video_graph,
    run_video_workflow,
    run_workflow,
)
from schemas.analysis import (
    AudioCharacteristics,
    SceneSegment,
    VideoProperties,
    VisualChange,
)
from schemas.audio_speakers import ConversationalStructure, ScoredSpan, SpeakerTurn
from schemas.base import JobStatus
from schemas.clips import ClipCandidate
from schemas.funny import FunnyMoment
from schemas.job import PIPELINE_STEPS, ProgressStepStatus, SourceType, VideoJobRequest
from schemas.moments import DetectedMoment
from schemas.project import ProjectMetadata
from schemas.scenes import DetectedScene
from schemas.transcript import (
    GeminiHook,
    GeminiScriptAnalysis,
    TranscriptAgentResult,
    WhisperSegment,
    WhisperTranscript,
    WhisperWord,
)
from schemas.viral import ViralMoment, ViralScoreBreakdown
from schemas.story import (
    GeminiClipScript,
    GeminiClipStory,
    GeminiScriptsBatch,
    GeminiStoriesBatch,
)
from schemas.localization import GeminiLocalizedBatch, GeminiLocalizedClip
from tools.moments.viral_detect import DISCLAIMER
from tools.whisper.adapter import whisper_to_structured
from tools.youtube.oembed_provider import OEmbedYouTubeProvider


def _fake_script_analysis(cleaned_text, sentences, sections) -> GeminiScriptAnalysis:
    return GeminiScriptAnalysis(
        language="English",
        topics=["demo"],
        section_titles=[f"Section {i + 1}" for i in range(len(sections))],
        hooks=[GeminiHook(sentence_index=0, reason="opener", score=0.8)],
        important_statements=[],
        clip_boundaries=[],
    )


def _install_mock_text_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "graph.workflow.TextAgent",
        lambda: TextAgent(analyze_fn=_fake_script_analysis),
    )


def _fake_transcribe(media_path):
    return {
        "language": "en",
        "text": "Hello from mock whisper",
        "model": "base",
        "segments": [
            WhisperSegment(
                id=0,
                start=0.0,
                end=1.0,
                text="Hello from mock whisper",
                words=[WhisperWord(word="Hello", start=0.0, end=0.3)],
                confidence=0.9,
            )
        ],
        "raw": {},
    }


def _install_mock_transcript_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agents.transcript_agent.extract_wav_for_asr",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "graph.workflow.TranscriptAgent",
        lambda: TranscriptAgent(transcribe_fn=_fake_transcribe),
    )


def _install_mock_understanding_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep CI fast: mock OpenCV/FFmpeg probes inside understanding agent."""

    def _probe(_path):
        return VideoProperties(
            duration_seconds=5.0,
            fps=30.0,
            width=640,
            height=360,
            frame_count=150,
            video_codec="h264",
            audio_codec="aac",
        )

    def _scenes(_path, **_kwargs):
        return {
            "sampled_frames": [],
            "scenes": [SceneSegment(id=0, start=0.0, end=5.0, score=0.0)],
            "visual_changes": [VisualChange(time_seconds=1.0, score=0.4, kind="cut")],
            "object_cues": [],
            "frames_analyzed": 5,
            "effective_sample_fps": 1.0,
        }

    def _audio(_path):
        return AudioCharacteristics(has_audio=True, sample_rate=44100, channels=2)

    monkeypatch.setattr(
        "graph.workflow.VideoUnderstandingAgent",
        lambda: VideoUnderstandingAgent(
            probe_fn=_probe,
            scenes_fn=_scenes,
            audio_fn=_audio,
        ),
    )


def _install_mock_scene_detection_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    def _detect(**_kwargs):
        return {
            "scenes": [
                DetectedScene(
                    id=0,
                    start=0.0,
                    end=5.0,
                    duration=5.0,
                    visual_change_score=0.4,
                    description="Hard cut (score=0.40)",
                    change_kinds=["cut"],
                )
            ],
            "duration": 5.0,
            "source_signals": {"visual": 1, "speaker": 0, "event": 0, "rescanned": 0},
            "notes": "",
        }

    monkeypatch.setattr(
        "graph.workflow.SceneDetectionAgent",
        lambda: SceneDetectionAgent(detect_fn=_detect),
    )


def _install_mock_audio_speaker_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    def _audio(**_kwargs):
        return {
            "silence_spans": [],
            "pause_spans": [],
            "volume_events": [],
            "intensity_spans": [],
            "laughter_candidates": [],
            "excitement_candidates": [],
            "question_spans": [
                ScoredSpan(
                    start=0.0,
                    end=1.0,
                    score=0.6,
                    label="question",
                    evidence_tags=["clip_boundary"],
                )
            ],
            "reaction_spans": [],
            "summary_scores": {
                "silence_ratio": 0.0,
                "speech_intensity": 0.3,
                "volume_dynamics": 0.0,
                "laughter": 0.0,
                "excitement": 0.0,
                "pause_density": 0.0,
                "question_density": 0.5,
                "reaction_density": 0.0,
            },
            "notes": "",
        }

    def _speakers(**_kwargs):
        return {
            "turns": [
                SpeakerTurn(
                    id=0, start=0.0, end=5.0, text_excerpt="hello", change_score=0.0
                )
            ],
            "speaker_change_candidates": [],
            "conversational_structure": ConversationalStructure(),
            "summary_scores": {"speaker_change_rate": 0.0, "turn_count": 1.0},
            "notes": "Speaker-independent turn heuristics — not true diarization.",
        }

    monkeypatch.setattr(
        "graph.workflow.AudioAnalysisAgent",
        lambda: AudioAnalysisAgent(analyze_fn=_audio),
    )
    monkeypatch.setattr(
        "graph.workflow.SpeakerAnalysisAgent",
        lambda: SpeakerAnalysisAgent(analyze_fn=_speakers),
    )


def _install_mock_moment_detection_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    def _analyze(**_kwargs):
        return [
            DetectedMoment(
                category="important",
                start=0.0,
                end=2.0,
                title="Key point",
                reason="hook",
                score=0.8,
                transcript="Key point",
                evidence=["transcript:hook"],
            )
        ]

    monkeypatch.setattr(
        "graph.workflow.MomentDetectionAgent",
        lambda: MomentDetectionAgent(analyze_fn=_analyze),
    )


def _install_mock_funny_moment_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    def _detect(**_kwargs):
        return [
            FunnyMoment(
                id=0,
                start=0.0,
                end=2.0,
                humor_kinds=["joke"],
                humor_score=0.7,
                explanation="signals=transcript,timing",
                transcript="Why did the chicken",
                suggested_title="Chicken setup",
                evidence=["transcript:joke_setup@0.0"],
            )
        ]

    monkeypatch.setattr(
        "graph.workflow.FunnyMomentAgent",
        lambda: FunnyMomentAgent(detect_fn=_detect),
    )


def _install_mock_viral_moment_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    def _detect(**_kwargs):
        return [
            ViralMoment(
                id=0,
                start=0.0,
                end=3.0,
                scores=ViralScoreBreakdown(hook=0.8, emotion=0.7),
                final_score=0.55,
                rank=1,
                explanation=DISCLAIMER,
                transcript="Hook line",
                suggested_title="Hook line",
                evidence=["seed:hook"],
            )
        ]

    monkeypatch.setattr(
        "graph.workflow.ViralMomentAgent",
        lambda: ViralMomentAgent(detect_fn=_detect),
    )


def _install_mock_smart_clip_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    def _select(**_kwargs):
        return [
            ClipCandidate(
                id=0,
                start=0.0,
                end=15.0,
                duration=15.0,
                transcript="Selected clip transcript.",
                category="important",
                score=0.8,
                hook="Selected clip transcript",
                reason="snapped to sentence boundaries",
                title="Selected clip",
                evidence=["seed:moments"],
            )
        ]

    monkeypatch.setattr(
        "graph.workflow.SmartClipAgent",
        lambda: SmartClipAgent(select_fn=_select),
    )


def _install_mock_story_script_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    def _stories(clip_blocks, **_kwargs) -> GeminiStoriesBatch:
        return GeminiStoriesBatch(
            stories=[
                GeminiClipStory(
                    clip_id=0,
                    hook="Hook from source",
                    context="Brief context",
                    value_event="Core value from clip",
                    payoff="Clear payoff",
                    cta="Follow for more",
                )
            ]
        )

    def _scripts(clip_blocks, **_kwargs) -> GeminiScriptsBatch:
        return GeminiScriptsBatch(
            scripts=[
                GeminiClipScript(
                    clip_id=0,
                    title="Selected Clip Title",
                    hook="Hook from source",
                    short_script="Hook from source. Brief context. Core value. Payoff. Follow.",
                    caption="Watch this clip.",
                    cta="Follow for more",
                    thumbnail_text="Must Watch",
                    keywords=["clip", "tips"],
                )
            ]
        )

    monkeypatch.setattr(
        "graph.workflow.StoryAgent",
        lambda: StoryAgent(generate_fn=_stories),
    )
    monkeypatch.setattr(
        "graph.workflow.ScriptAgent",
        lambda: ScriptAgent(generate_fn=_scripts),
    )


def _install_mock_language_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    def _localize(script_blocks, *, locale_block: str = "", **_kwargs) -> GeminiLocalizedBatch:
        return GeminiLocalizedBatch(
            scripts=[
                GeminiLocalizedClip(
                    clip_id=0,
                    title="Localized Title",
                    hook="Localized hook",
                    short_script="Localized short script.",
                    caption="Localized caption",
                    cta="Follow",
                    thumbnail_text="Watch",
                    keywords=["local"],
                    voice_direction="Neutral clear voice",
                )
            ]
        )

    monkeypatch.setattr(
        "graph.workflow.LanguageAgent",
        lambda: LanguageAgent(localize_fn=_localize),
    )


def _install_passthrough_transcript_for_youtube(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """YouTube metadata-only path: inject a successful stub TranscriptAgent result."""

    class _StubTranscriptAgent:
        def run(self, project, project_dir=None, source_metadata=None, **_):
            meta = (
                project
                if isinstance(project, ProjectMetadata)
                else ProjectMetadata.model_validate(project)
            )
            speech = WhisperTranscript(
                project_id=meta.project_id,
                source_type=meta.source_type,
                media_path="",
                language="en",
                segments=[
                    WhisperSegment(id=0, start=0.0, end=1.0, text="Stub youtube audio")
                ],
                text="Stub youtube audio",
                model="base",
            )
            structured = whisper_to_structured(speech)
            return TranscriptAgentResult(
                speech_transcript=speech,
                structured_transcript=structured,
                transcript_path=str(
                    Path(project_dir or ".") / "transcripts" / "transcript.json"
                ),
                messages=["[transcript] stubbed for youtube test"],
            )

    monkeypatch.setattr("graph.workflow.TranscriptAgent", _StubTranscriptAgent)


def _install_mock_youtube_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock(spec=httpx.Client)

    def _get(url: str, params=None, **_kwargs):
        response = MagicMock()
        response.status_code = 200
        if "oembed" in url:
            response.json.return_value = {
                "title": "Workflow Test Video",
                "author_name": "Workflow Channel",
                "type": "video",
            }
        else:
            response.json.return_value = {"items": []}
        return response

    client.get.side_effect = _get
    provider = OEmbedYouTubeProvider(client=client)
    monkeypatch.setattr(
        "agents.youtube_agent.get_youtube_provider",
        lambda: provider,
    )
    monkeypatch.setattr(
        "graph.workflow.YouTubeAgent",
        lambda: __import__("agents.youtube_agent", fromlist=["YouTubeAgent"]).YouTubeAgent(
            provider=provider
        ),
    )


def test_build_graph_compiles() -> None:
    assert build_graph() is not None
    assert build_video_graph() is not None


def test_step_node_count() -> None:
    assert len(PIPELINE_STEPS) == 15
    assert "input_agent" in STEP_NODE_NAMES
    assert "youtube_ingest" in STEP_NODE_NAMES
    assert "script_ingest" in STEP_NODE_NAMES
    assert TRANSCRIPT_NODE in STEP_NODE_NAMES
    assert UNDERSTANDING_NODE in STEP_NODE_NAMES
    assert SCENE_DETECTION_NODE in STEP_NODE_NAMES
    assert AUDIO_ANALYSIS_NODE in STEP_NODE_NAMES
    assert SPEAKER_ANALYSIS_NODE in STEP_NODE_NAMES
    assert FUNNY_MOMENT_NODE in STEP_NODE_NAMES
    assert VIRAL_MOMENT_NODE in STEP_NODE_NAMES
    assert MOMENT_DETECTION_NODE in STEP_NODE_NAMES
    assert SMART_CLIP_NODE in STEP_NODE_NAMES
    assert "research" in STEP_NODE_NAMES
    assert "supervisor" in STEP_NODE_NAMES
    assert "storyboard" in STEP_NODE_NAMES
    assert "analytics" in STEP_NODE_NAMES
    assert VIDEO_TYPE_NODE in STEP_NODE_NAMES
    assert VISUAL_STYLE_NODE in STEP_NODE_NAMES
    assert ENVIRONMENT_NODE in STEP_NODE_NAMES
    assert STORY_NODE in STEP_NODE_NAMES
    assert SCRIPT_NODE in STEP_NODE_NAMES
    assert COUNTRY_NODE in STEP_NODE_NAMES
    assert REGIONAL_NODE in STEP_NODE_NAMES
    assert CULTURAL_NODE in STEP_NODE_NAMES
    assert HUMOR_NODE in STEP_NODE_NAMES
    assert LANGUAGE_NODE in STEP_NODE_NAMES
    assert BROLL_NODE in STEP_NODE_NAMES
    assert VOICE_NODE in STEP_NODE_NAMES
    assert MUSIC_NODE in STEP_NODE_NAMES
    assert CAPTIONS_NODE in STEP_NODE_NAMES
    assert REFRAME_NODE in STEP_NODE_NAMES
    assert PLATFORM_NODE in STEP_NODE_NAMES
    assert RENDER_NODE in STEP_NODE_NAMES
    assert QUALITY_NODE in STEP_NODE_NAMES
    assert EXPORT_NODE in STEP_NODE_NAMES
    assert len(STEP_NODE_NAMES) >= 15
    # PROMPT 25: story/script before creative type/style/env; moments before funny/viral
    assert STEP_NODE_NAMES.index(MOMENT_DETECTION_NODE) < STEP_NODE_NAMES.index(
        FUNNY_MOMENT_NODE
    )
    assert STEP_NODE_NAMES.index(FUNNY_MOMENT_NODE) < STEP_NODE_NAMES.index(
        VIRAL_MOMENT_NODE
    )
    assert STEP_NODE_NAMES.index(VIRAL_MOMENT_NODE) < STEP_NODE_NAMES.index(
        SMART_CLIP_NODE
    )
    assert STEP_NODE_NAMES.index(SMART_CLIP_NODE) < STEP_NODE_NAMES.index("research")
    assert STEP_NODE_NAMES.index("research") < STEP_NODE_NAMES.index(STORY_NODE)
    assert STEP_NODE_NAMES.index(STORY_NODE) < STEP_NODE_NAMES.index(SCRIPT_NODE)
    assert STEP_NODE_NAMES.index(SCRIPT_NODE) < STEP_NODE_NAMES.index("storyboard")
    assert STEP_NODE_NAMES.index("storyboard") < STEP_NODE_NAMES.index(COUNTRY_NODE)
    assert STEP_NODE_NAMES.index(COUNTRY_NODE) < STEP_NODE_NAMES.index(REGIONAL_NODE)
    assert STEP_NODE_NAMES.index(REGIONAL_NODE) < STEP_NODE_NAMES.index(LANGUAGE_NODE)
    assert STEP_NODE_NAMES.index(LANGUAGE_NODE) < STEP_NODE_NAMES.index(CULTURAL_NODE)
    assert STEP_NODE_NAMES.index(CULTURAL_NODE) < STEP_NODE_NAMES.index(HUMOR_NODE)
    assert STEP_NODE_NAMES.index(HUMOR_NODE) < STEP_NODE_NAMES.index(VIDEO_TYPE_NODE)
    assert STEP_NODE_NAMES.index(VIDEO_TYPE_NODE) < STEP_NODE_NAMES.index(
        VISUAL_STYLE_NODE
    )
    assert STEP_NODE_NAMES.index(VISUAL_STYLE_NODE) < STEP_NODE_NAMES.index(
        ENVIRONMENT_NODE
    )
    assert STEP_NODE_NAMES.index(ENVIRONMENT_NODE) < STEP_NODE_NAMES.index(BROLL_NODE)
    # broll → … → captions → smart_reframe → platform → render → quality → analytics → export
    assert STEP_NODE_NAMES.index(BROLL_NODE) < STEP_NODE_NAMES.index(VOICE_NODE)
    assert STEP_NODE_NAMES.index(VOICE_NODE) < STEP_NODE_NAMES.index(MUSIC_NODE)
    assert STEP_NODE_NAMES.index(MUSIC_NODE) < STEP_NODE_NAMES.index(CAPTIONS_NODE)
    assert STEP_NODE_NAMES.index(CAPTIONS_NODE) < STEP_NODE_NAMES.index(REFRAME_NODE)
    assert STEP_NODE_NAMES.index(REFRAME_NODE) < STEP_NODE_NAMES.index(PLATFORM_NODE)
    assert STEP_NODE_NAMES.index(PLATFORM_NODE) < STEP_NODE_NAMES.index(RENDER_NODE)
    assert STEP_NODE_NAMES.index(RENDER_NODE) < STEP_NODE_NAMES.index(QUALITY_NODE)
    assert STEP_NODE_NAMES.index(QUALITY_NODE) < STEP_NODE_NAMES.index("analytics")
    assert STEP_NODE_NAMES.index("analytics") < STEP_NODE_NAMES.index(EXPORT_NODE)
    # No stub step_* nodes remain
    assert not any(n.startswith("step_14_") for n in STEP_NODE_NAMES)
    assert not any(n.startswith("step_13_") for n in STEP_NODE_NAMES)
    assert not any(n.startswith("step_12_") for n in STEP_NODE_NAMES)
    assert not any(n.startswith("step_11_") for n in STEP_NODE_NAMES)
    assert not any(n.startswith("step_10_") for n in STEP_NODE_NAMES)
    assert not any(n.startswith("step_09_") for n in STEP_NODE_NAMES)
    assert not any(n.startswith("step_08_") for n in STEP_NODE_NAMES)


def test_run_video_workflow_completes_all_steps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("YOUTUBE_DOWNLOAD_ENABLED", "false")
    get_settings.cache_clear()
    _install_mock_text_agent(monkeypatch)
    _install_mock_story_script_agents(monkeypatch)
    _install_mock_language_agent(monkeypatch)

    request = VideoJobRequest(
        source_type=SourceType.SCRIPT,
        script_text="smoke-test script. Second sentence for structure.",
    )
    result = run_video_workflow(request)

    assert result["status"] == JobStatus.COMPLETED.value
    assert result["error"] is None
    assert result["result"] is not None
    assert result["project"] is not None
    assert result["project"]["source_type"] == SourceType.SCRIPT.value
    assert result["project_dir"] is not None
    assert Path(result["project_dir"]).is_dir()
    assert (Path(result["project_dir"]) / "project.json").is_file()
    assert result["next_agent"] == "script_ingest"
    assert result["transcript"] is not None
    assert (Path(result["project_dir"]) / "transcript.json").is_file()
    assert result["analysis"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "video_analysis.json").is_file()
    assert result["scenes"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "scenes.json").is_file()
    assert result["audio_analysis"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "audio_analysis.json").is_file()
    assert result["speakers"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "speakers.json").is_file()
    assert result["funny_moments"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "funny_moments.json").is_file()
    assert result["viral_moments"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "viral_moments.json").is_file()
    assert result["moments"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "moments.json").is_file()
    assert result["clips"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "clips.json").is_file()
    assert result["video_type_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "video_type.json").is_file()
    assert result["visual_style_pack"] is not None
    assert result["visual_style_pack"]["plan"]["summary"]
    assert (Path(result["project_dir"]) / "analysis" / "visual_style.json").is_file()
    assert result["environment_pack"] is not None
    assert result["environment_pack"]["plan"]["summary"]
    assert (Path(result["project_dir"]) / "analysis" / "environment.json").is_file()
    assert result["stories"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "stories.json").is_file()
    assert result["scripts"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "scripts.json").is_file()
    assert result["localizations"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "localizations.json").is_file()
    assert (Path(result["project_dir"]) / "analysis" / "locale_context.json").is_file()
    assert result["cultural_adaptation"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "cultural_adaptation.json").is_file()
    assert result["humor_localization"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "humor_localization.json").is_file()
    assert result["broll_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "broll_plan.json").is_file()
    assert result["voice_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "voice_plan.json").is_file()
    assert result["music_pack"] is not None
    assert result["music_pack"]["plan"]["generation_required"] is False
    assert (Path(result["project_dir"]) / "analysis" / "music_plan.json").is_file()
    assert result["captions_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "captions_plan.json").is_file()
    assert result["reframe_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "reframe_plan.json").is_file()
    assert result["platform_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "platform_plan.json").is_file()
    assert (Path(result["project_dir"]) / "exports" / "platform_metadata.json").is_file()
    assert result["platform_pack"]["plan"]["export_hints"]["publish_status"] == (
        "not_published"
    )
    assert result["render_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "render_plan.json").is_file()
    assert result["quality_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "quality_report.json").is_file()
    assert result["export_pack"] is not None
    assert (Path(result["project_dir"]) / "exports" / "manifest.json").is_file()
    # Script path: honest soft-skip (no silent broken video)
    assert result["render_pack"]["plan"]["encoded"] is False
    assert result["quality_pack"]["report"]["skipped"] is True
    assert result["result"]["export_path"]
    assert result["result"]["export_pack"] is not None
    # PROMPT 25 dual-write aliases
    root = Path(result["project_dir"])
    assert (root / "localization.json").is_file()
    assert (root / "video_plan.json").is_file()
    assert (root / "subtitles").is_dir()
    assert (root / "final").is_dir()
    assert (root / "thumbnails").is_dir()
    assert result["result"].get("output_files") is not None

    steps = result["steps"]
    assert len(steps) == 15
    assert all(s["status"] == ProgressStepStatus.COMPLETED.value for s in steps)

    get_settings.cache_clear()


def test_run_workflow_compat_wrapper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("YOUTUBE_DOWNLOAD_ENABLED", "false")
    get_settings.cache_clear()
    _install_mock_text_agent(monkeypatch)
    _install_mock_story_script_agents(monkeypatch)
    _install_mock_language_agent(monkeypatch)

    result = run_workflow("smoke-test. Another line.")
    assert result["status"] == JobStatus.COMPLETED.value
    assert result["job"]["source_type"] == SourceType.SCRIPT.value
    assert result["job"]["script_text"] == "smoke-test. Another line."
    assert result["project"] is not None
    assert result["transcript"] is not None
    assert result["analysis"] is not None
    assert result["scenes"] is not None
    assert result["audio_analysis"] is not None
    assert result["speakers"] is not None
    assert result["funny_moments"] is not None
    assert result["viral_moments"] is not None
    assert result["moments"] is not None
    assert result["clips"] is not None
    assert result["stories"] is not None
    assert result["scripts"] is not None
    assert result["localizations"] is not None
    assert result["cultural_adaptation"] is not None
    assert result["humor_localization"] is not None

    get_settings.cache_clear()


def test_on_step_callback_invoked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("YOUTUBE_DOWNLOAD_ENABLED", "false")
    get_settings.cache_clear()
    _install_mock_youtube_provider(monkeypatch)
    _install_passthrough_transcript_for_youtube(monkeypatch)
    _install_mock_story_script_agents(monkeypatch)
    _install_mock_language_agent(monkeypatch)

    seen: list[int] = []

    def _on_step(state: dict) -> None:
        seen.append(state.get("current_step", -1))

    request = VideoJobRequest(
        source_type=SourceType.YOUTUBE,
        youtube_url="https://youtu.be/abcdefghijk",
    )
    run_video_workflow(request, on_step=_on_step)
    assert len(seen) >= 15
    get_settings.cache_clear()


def test_youtube_workflow_sets_route_and_source_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("YOUTUBE_DOWNLOAD_ENABLED", "false")
    get_settings.cache_clear()
    _install_mock_youtube_provider(monkeypatch)
    _install_passthrough_transcript_for_youtube(monkeypatch)
    _install_mock_story_script_agents(monkeypatch)
    _install_mock_language_agent(monkeypatch)

    request = VideoJobRequest(
        source_type=SourceType.YOUTUBE,
        youtube_url="https://www.youtube.com/watch?v=abcdefghijk",
    )
    result = run_video_workflow(request)
    assert result["next_agent"] == "youtube_ingest"
    assert result["project"]["youtube_url"]
    assert result["source_metadata"] is not None
    assert result["source_metadata"]["title"] == "Workflow Test Video"
    assert result["source_dir"] is not None
    assert Path(result["source_dir"]).is_dir()
    assert (Path(result["source_dir"]) / "source_metadata.json").is_file()
    assert result["status"] == JobStatus.COMPLETED.value
    assert result["speech_transcript"] is not None
    assert result["analysis"] is not None
    assert result["scenes"] is not None
    assert result["audio_analysis"] is not None
    assert result["speakers"] is not None
    assert result["funny_moments"] is not None
    assert result["viral_moments"] is not None
    assert result["moments"] is not None
    assert result["clips"] is not None
    assert result["stories"] is not None
    assert result["scripts"] is not None
    assert result["localizations"] is not None
    get_settings.cache_clear()


def test_upload_workflow_runs_whisper_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    get_settings.cache_clear()
    _install_mock_transcript_agent(monkeypatch)
    _install_mock_understanding_agent(monkeypatch)
    _install_mock_scene_detection_agent(monkeypatch)
    _install_mock_audio_speaker_agents(monkeypatch)
    _install_mock_funny_moment_agent(monkeypatch)
    _install_mock_viral_moment_agent(monkeypatch)
    _install_mock_moment_detection_agent(monkeypatch)
    _install_mock_smart_clip_agent(monkeypatch)
    _install_mock_story_script_agents(monkeypatch)
    _install_mock_language_agent(monkeypatch)

    video = tmp_path / "upload.mp4"
    video.write_bytes(b"fake")

    request = VideoJobRequest(
        job_id="upload-job-1",
        source_type=SourceType.UPLOAD,
        upload_path=str(video),
    )
    result = run_video_workflow(request)
    assert result["status"] == JobStatus.COMPLETED.value
    assert result["speech_transcript"] is not None
    assert result["speech_transcript"]["language"] == "en"
    assert result["transcript"] is not None
    speech_path = Path(result["project_dir"]) / "transcripts" / "transcript.json"
    assert speech_path.is_file()
    assert result["analysis"] is not None
    assert result["analysis"]["properties"]["duration_seconds"] == 5.0
    assert (Path(result["project_dir"]) / "analysis" / "video_analysis.json").is_file()
    assert result["scenes"] is not None
    assert result["scenes"]["scenes"][0]["duration"] == 5.0
    assert (Path(result["project_dir"]) / "analysis" / "scenes.json").is_file()
    assert result["audio_analysis"] is not None
    assert result["audio_analysis"]["summary_scores"]["question_density"] == 0.5
    assert (Path(result["project_dir"]) / "analysis" / "audio_analysis.json").is_file()
    assert result["speakers"] is not None
    assert result["speakers"]["turns"]
    assert (Path(result["project_dir"]) / "analysis" / "speakers.json").is_file()
    assert result["funny_moments"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "funny_moments.json").is_file()
    assert result["viral_moments"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "viral_moments.json").is_file()
    assert result["moments"] is not None
    assert result["moments"]["moments"][0]["category"] == "important"
    assert (Path(result["project_dir"]) / "analysis" / "moments.json").is_file()
    assert result["clips"] is not None
    assert result["clips"]["clips"][0]["hook"]
    assert (Path(result["project_dir"]) / "analysis" / "clips.json").is_file()
    assert result["video_type_pack"] is not None
    assert result["video_type_pack"]["preset"]["name"]
    assert (Path(result["project_dir"]) / "analysis" / "video_type.json").is_file()
    assert result["visual_style_pack"] is not None
    assert result["visual_style_pack"]["plan"]["summary"]
    assert (Path(result["project_dir"]) / "analysis" / "visual_style.json").is_file()
    assert result["environment_pack"] is not None
    assert result["environment_pack"]["plan"]["summary"]
    assert (Path(result["project_dir"]) / "analysis" / "environment.json").is_file()
    assert result["stories"] is not None
    assert result["stories"]["stories"][0]["structure"]["hook"]
    assert (Path(result["project_dir"]) / "analysis" / "stories.json").is_file()
    assert result["scripts"] is not None
    assert result["scripts"]["scripts"][0]["title"]
    assert (Path(result["project_dir"]) / "analysis" / "scripts.json").is_file()
    assert result["localizations"] is not None
    assert result["localizations"]["versions"]
    assert (Path(result["project_dir"]) / "analysis" / "localizations.json").is_file()
    assert result["cultural_adaptation"] is not None
    assert result["humor_localization"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "cultural_adaptation.json").is_file()
    assert (Path(result["project_dir"]) / "analysis" / "humor_localization.json").is_file()
    assert result["broll_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "broll_plan.json").is_file()
    assert result["voice_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "voice_plan.json").is_file()
    assert result["music_pack"] is not None
    assert result["music_pack"]["plan"]["generation_required"] is False
    assert (Path(result["project_dir"]) / "analysis" / "music_plan.json").is_file()
    assert result["captions_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "captions_plan.json").is_file()
    assert result["reframe_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "reframe_plan.json").is_file()
    assert result["platform_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "platform_plan.json").is_file()
    assert (Path(result["project_dir"]) / "exports" / "platform_metadata.json").is_file()
    assert result["render_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "render_plan.json").is_file()
    assert result["quality_pack"] is not None
    assert (Path(result["project_dir"]) / "analysis" / "quality_report.json").is_file()
    assert result["export_pack"] is not None
    assert (Path(result["project_dir"]) / "exports" / "manifest.json").is_file()
    get_settings.cache_clear()
