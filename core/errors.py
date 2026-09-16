"""Application-specific exception hierarchy."""

from __future__ import annotations


class VideoAgentError(Exception):
    """Base error for the AI Creator OS."""


class ConfigurationError(VideoAgentError):
    """Raised when configuration is missing or invalid."""


class WorkflowError(VideoAgentError):
    """Raised when a LangGraph workflow step fails."""


class StorageError(VideoAgentError):
    """Raised when local filesystem storage operations fail."""


class InputValidationError(VideoAgentError):
    """Raised when user input fails Input Agent validation."""


class YouTubeAgentError(VideoAgentError):
    """Raised when YouTube URL validation or metadata preparation fails."""


class TextAgentError(VideoAgentError):
    """Raised when Text/Script Agent processing fails."""


class TranscriptAgentError(VideoAgentError):
    """Raised when Whisper Transcript Agent processing fails."""


class VideoUnderstandingError(VideoAgentError):
    """Raised when Video Understanding Agent analysis fails."""


class SceneDetectionError(VideoAgentError):
    """Raised when Scene Detection Agent processing fails."""


class AudioAnalysisError(VideoAgentError):
    """Raised when Audio Analysis Agent processing fails."""


class SpeakerAnalysisError(VideoAgentError):
    """Raised when Speaker Analysis Agent processing fails."""


class MomentDetectionError(VideoAgentError):
    """Raised when Moment Detection Agent processing fails."""


class FunnyMomentError(VideoAgentError):
    """Raised when Funny Moment Agent processing fails."""


class ViralMomentError(VideoAgentError):
    """Raised when Viral Moment Agent processing fails."""


class SmartClipError(VideoAgentError):
    """Raised when Smart Clip Selection Agent processing fails."""


class StoryAgentError(VideoAgentError):
    """Raised when Story Agent generation fails."""


class ScriptAgentError(VideoAgentError):
    """Raised when Script Agent generation fails."""


class SupervisorAgentError(VideoAgentError):
    """Raised when Supervisor Agent intake planning fails."""


class ResearchAgentError(VideoAgentError):
    """Raised when Research Agent / Parallel Search fails."""


class StoryboardAgentError(VideoAgentError):
    """Raised when Storyboard Agent generation fails."""


class AnalyticsAgentError(VideoAgentError):
    """Raised when Analytics Agent rollup fails."""


class CountryAgentError(VideoAgentError):
    """Raised when Country Agent localization resolution fails."""


class RegionalAgentError(VideoAgentError):
    """Raised when Regional Agent localization resolution fails."""


class LanguageAgentError(VideoAgentError):
    """Raised when Language Agent localization fails."""


class CulturalAdaptationError(VideoAgentError):
    """Raised when Cultural Adaptation Agent processing fails."""


class HumorLocalizationError(VideoAgentError):
    """Raised when Humor Localization Agent processing fails."""


class VideoTypeAgentError(VideoAgentError):
    """Raised when Video Type Agent preset resolution fails."""


class VisualStyleAgentError(VideoAgentError):
    """Raised when Visual Style Agent preset resolution fails."""


class EnvironmentAgentError(VideoAgentError):
    """Raised when Environment Agent preset resolution fails."""


class BRollAgentError(VideoAgentError):
    """Raised when B-Roll Agent planning fails."""


class VoiceAgentError(VideoAgentError):
    """Raised when Voice Agent planning fails."""


class MusicAgentError(VideoAgentError):
    """Raised when Music Agent planning fails."""


class CaptionAgentError(VideoAgentError):
    """Raised when Caption Agent planning or export fails."""


class ReframeAgentError(VideoAgentError):
    """Raised when Smart Reframe Agent planning or encoding fails."""


class PlatformAgentError(VideoAgentError):
    """Raised when Platform Agent optimization or export metadata fails."""


class RenderAgentError(VideoAgentError):
    """Raised when Render Agent composition fails."""


class QualityAgentError(VideoAgentError):
    """Raised when Quality Agent validation fails after correction attempts."""


class ExportAgentError(VideoAgentError):
    """Raised when Export Agent packaging fails."""
