"""Agent implementations for the AI Creator OS."""

from agents.analytics_agent import AnalyticsAgent
from agents.audio_analysis_agent import AudioAnalysisAgent
from agents.base import BaseAgent, PlaceholderAgent
from agents.broll_agent import BRollAgent
from agents.caption_agent import CaptionAgent
from agents.country_agent import CountryAgent
from agents.cultural_adaptation_agent import CulturalAdaptationAgent
from agents.environment_agent import EnvironmentAgent
from agents.export_agent import ExportAgent
from agents.funny_moment_agent import FunnyMomentAgent
from agents.humor_localization_agent import HumorLocalizationAgent
from agents.input_agent import InputAgent, route_for_source
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
from agents.video_understanding_agent import VideoUnderstandingAgent
from agents.video_type_agent import VideoTypeAgent
from agents.visual_style_agent import VisualStyleAgent
from agents.viral_moment_agent import ViralMomentAgent
from agents.voice_agent import VoiceAgent
from agents.youtube_agent import YouTubeAgent

__all__ = [
    "BaseAgent",
    "PlaceholderAgent",
    "AnalyticsAgent",
    "AudioAnalysisAgent",
    "BRollAgent",
    "CaptionAgent",
    "CountryAgent",
    "CulturalAdaptationAgent",
    "EnvironmentAgent",
    "ExportAgent",
    "FunnyMomentAgent",
    "HumorLocalizationAgent",
    "InputAgent",
    "route_for_source",
    "LanguageAgent",
    "LocalVideoIngestAgent",
    "MomentDetectionAgent",
    "MusicAgent",
    "PlatformAgent",
    "QualityAgent",
    "RegionalAgent",
    "ReframeAgent",
    "RenderAgent",
    "ResearchAgent",
    "SceneDetectionAgent",
    "ScriptAgent",
    "SmartClipAgent",
    "SpeakerAnalysisAgent",
    "StoryAgent",
    "StoryboardAgent",
    "SupervisorAgent",
    "TextAgent",
    "TranscriptAgent",
    "VideoUnderstandingAgent",
    "VideoTypeAgent",
    "VisualStyleAgent",
    "ViralMomentAgent",
    "VoiceAgent",
    "YouTubeAgent",
]
