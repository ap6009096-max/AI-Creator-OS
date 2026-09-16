"""Gemini chat model helpers via LangChain."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import get_settings
from core.errors import (
    ConfigurationError,
    CulturalAdaptationError,
    HumorLocalizationError,
    LanguageAgentError,
    ResearchAgentError,
    ScriptAgentError,
    StoryAgentError,
    StoryboardAgentError,
    TextAgentError,
)
from core.logging import get_logger
from prompts.cultural_adaptation_agent import (
    CULTURAL_ADAPTATION_SYSTEM,
    build_cultural_adaptation_user_prompt,
)
from prompts.humor_localization_agent import (
    HUMOR_LOCALIZATION_SYSTEM,
    build_humor_localization_user_prompt,
)
from prompts.language_agent import LANGUAGE_AGENT_SYSTEM, build_language_agent_user_prompt
from prompts.research_agent import (
    RESEARCH_AGENT_SYSTEM,
    build_research_agent_user_prompt,
)
from prompts.script_agent import SCRIPT_AGENT_SYSTEM, build_script_agent_user_prompt
from prompts.story_agent import STORY_AGENT_SYSTEM, build_story_agent_user_prompt
from prompts.storyboard_agent import (
    STORYBOARD_AGENT_SYSTEM,
    build_storyboard_agent_user_prompt,
)
from prompts.text_agent import TEXT_AGENT_SYSTEM, build_text_agent_user_prompt
from schemas.localization import (
    GeminiCulturalBatch,
    GeminiHumorBatch,
    GeminiLocalizedBatch,
)
from schemas.research import GeminiResearchPlan
from schemas.story import GeminiScriptsBatch, GeminiStoriesBatch
from schemas.storyboard import GeminiStoryboardBatch
from schemas.transcript import (
    GeminiScriptAnalysis,
    ScriptSection,
    ScriptSentence,
)

logger = get_logger(__name__)


def get_chat_model(*, temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Return a configured Gemini chat model (requires GEMINI_API_KEY)."""
    settings = get_settings()
    api_key = settings.require_gemini_api_key()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=api_key,
        temperature=temperature,
    )


def analyze_script_structure(
    cleaned_text: str,
    sentences: list[ScriptSentence],
    sections: list[ScriptSection],
    *,
    model: Any | None = None,
) -> GeminiScriptAnalysis:
    """Run structured Gemini analysis over a cleaned script."""
    if not cleaned_text.strip():
        raise TextAgentError("Cannot analyze empty script text.")

    sentence_lines = [f"{s.index}: {s.text}" for s in sentences]
    section_summaries = [
        f"{i}: chars {sec.start_char}-{sec.end_char}: {cleaned_text[sec.start_char:sec.end_char][:160]}"
        for i, sec in enumerate(sections)
    ]
    user_prompt = build_text_agent_user_prompt(
        cleaned_text, sentence_lines, section_summaries
    )

    try:
        chat = model or get_chat_model()
        structured = chat.with_structured_output(GeminiScriptAnalysis)
        result = structured.invoke(
            [
                SystemMessage(content=TEXT_AGENT_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini script analysis failed")
        raise TextAgentError(f"Gemini script analysis failed: {exc}") from exc

    if isinstance(result, GeminiScriptAnalysis):
        return result
    if isinstance(result, dict):
        return GeminiScriptAnalysis.model_validate(result)
    raise TextAgentError("Unexpected Gemini structured output type.")


def generate_clip_stories(
    clip_blocks: list[str],
    *,
    video_type: str = "Shorts",
    country: str = "",
    video_type_block: str = "",
    visual_style_block: str = "",
    environment_block: str = "",
    model: Any | None = None,
) -> GeminiStoriesBatch:
    """Generate HOOK→CONTEXT→VALUE/EVENT→PAYOFF→CTA structures for clips."""
    if not clip_blocks:
        return GeminiStoriesBatch(stories=[])

    user_prompt = build_story_agent_user_prompt(
        clip_blocks,
        video_type=video_type,
        country=country,
        video_type_block=video_type_block,
        visual_style_block=visual_style_block,
        environment_block=environment_block,
    )
    try:
        chat = model or get_chat_model(temperature=0.3)
        structured = chat.with_structured_output(GeminiStoriesBatch)
        result = structured.invoke(
            [
                SystemMessage(content=STORY_AGENT_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini story generation failed")
        raise StoryAgentError(f"Gemini story generation failed: {exc}") from exc

    if isinstance(result, GeminiStoriesBatch):
        return result
    if isinstance(result, dict):
        return GeminiStoriesBatch.model_validate(result)
    raise StoryAgentError("Unexpected Gemini story structured output type.")


def generate_clip_scripts(
    clip_blocks: list[str],
    *,
    video_type: str = "Shorts",
    country: str = "",
    video_type_block: str = "",
    visual_style_block: str = "",
    environment_block: str = "",
    model: Any | None = None,
) -> GeminiScriptsBatch:
    """Generate title/hook/script/caption/CTA/thumbnail/keywords for clips."""
    if not clip_blocks:
        return GeminiScriptsBatch(scripts=[])

    user_prompt = build_script_agent_user_prompt(
        clip_blocks,
        video_type=video_type,
        country=country,
        video_type_block=video_type_block,
        visual_style_block=visual_style_block,
        environment_block=environment_block,
    )
    try:
        chat = model or get_chat_model(temperature=0.35)
        structured = chat.with_structured_output(GeminiScriptsBatch)
        result = structured.invoke(
            [
                SystemMessage(content=SCRIPT_AGENT_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini script generation failed")
        raise ScriptAgentError(f"Gemini script generation failed: {exc}") from exc

    if isinstance(result, GeminiScriptsBatch):
        return result
    if isinstance(result, dict):
        return GeminiScriptsBatch.model_validate(result)
    raise ScriptAgentError("Unexpected Gemini script structured output type.")


def localize_clip_scripts(
    script_blocks: list[str],
    *,
    locale_block: str,
    model: Any | None = None,
) -> GeminiLocalizedBatch:
    """Naturally localize clip scripts for one locale pack."""
    if not script_blocks:
        return GeminiLocalizedBatch(scripts=[])

    user_prompt = build_language_agent_user_prompt(locale_block, script_blocks)
    try:
        chat = model or get_chat_model(temperature=0.4)
        structured = chat.with_structured_output(GeminiLocalizedBatch)
        result = structured.invoke(
            [
                SystemMessage(content=LANGUAGE_AGENT_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini localization failed")
        raise LanguageAgentError(f"Gemini localization failed: {exc}") from exc

    if isinstance(result, GeminiLocalizedBatch):
        return result
    if isinstance(result, dict):
        return GeminiLocalizedBatch.model_validate(result)
    raise LanguageAgentError("Unexpected Gemini localization structured output type.")


def analyze_cultural_adaptation(
    script_blocks: list[str],
    *,
    locale_block: str,
    audience: str = "General",
    model: Any | None = None,
) -> GeminiCulturalBatch:
    """Analyze scripts for cultural adaptation findings."""
    if not script_blocks:
        return GeminiCulturalBatch(findings=[], cultural_summary="")

    user_prompt = build_cultural_adaptation_user_prompt(
        locale_block, audience, script_blocks
    )
    try:
        chat = model or get_chat_model(temperature=0.3)
        structured = chat.with_structured_output(GeminiCulturalBatch)
        result = structured.invoke(
            [
                SystemMessage(content=CULTURAL_ADAPTATION_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini cultural adaptation failed")
        raise CulturalAdaptationError(
            f"Gemini cultural adaptation failed: {exc}"
        ) from exc

    if isinstance(result, GeminiCulturalBatch):
        return result
    if isinstance(result, dict):
        return GeminiCulturalBatch.model_validate(result)
    raise CulturalAdaptationError("Unexpected Gemini cultural structured output type.")


def plan_humor_localization(
    script_blocks: list[str],
    *,
    mode: str,
    humor_style: str = "None",
    audience: str = "General",
    locale_block: str = "",
    cultural_summary: str = "",
    model: Any | None = None,
) -> GeminiHumorBatch:
    """Plan humor localization strategies per clip."""
    if not script_blocks:
        return GeminiHumorBatch(items=[], humor_summary="")

    user_prompt = build_humor_localization_user_prompt(
        mode=mode,
        humor_style=humor_style,
        audience=audience,
        locale_block=locale_block,
        cultural_summary=cultural_summary,
        script_blocks=script_blocks,
    )
    try:
        chat = model or get_chat_model(temperature=0.35)
        structured = chat.with_structured_output(GeminiHumorBatch)
        result = structured.invoke(
            [
                SystemMessage(content=HUMOR_LOCALIZATION_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini humor localization failed")
        raise HumorLocalizationError(
            f"Gemini humor localization failed: {exc}"
        ) from exc

    if isinstance(result, GeminiHumorBatch):
        return result
    if isinstance(result, dict):
        return GeminiHumorBatch.model_validate(result)
    raise HumorLocalizationError("Unexpected Gemini humor structured output type.")


def generate_research_plan(
    *,
    topic_hint: str,
    video_type: str = "Shorts",
    platform: str = "",
    audience: str = "",
    clip_summaries: list[str] | None = None,
    model: Any | None = None,
) -> GeminiResearchPlan:
    """Plan Parallel Search objective + keyword queries via Gemini."""
    user_prompt = build_research_agent_user_prompt(
        topic_hint=topic_hint,
        video_type=video_type,
        platform=platform,
        audience=audience,
        clip_summaries=clip_summaries,
    )
    try:
        chat = model or get_chat_model(temperature=0.2)
        structured = chat.with_structured_output(GeminiResearchPlan)
        result = structured.invoke(
            [
                SystemMessage(content=RESEARCH_AGENT_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini research plan failed")
        raise ResearchAgentError(f"Gemini research plan failed: {exc}") from exc

    if isinstance(result, GeminiResearchPlan):
        return result
    if isinstance(result, dict):
        return GeminiResearchPlan.model_validate(result)
    raise ResearchAgentError("Unexpected Gemini research plan structured output type.")


def generate_storyboard(
    *,
    script_blocks: list[str],
    story_blocks: list[str] | None = None,
    video_type: str = "Shorts",
    model: Any | None = None,
) -> GeminiStoryboardBatch:
    """Generate ordered storyboard frames from scripts/stories."""
    if not script_blocks and not (story_blocks or []):
        return GeminiStoryboardBatch(frames=[])

    user_prompt = build_storyboard_agent_user_prompt(
        script_blocks=script_blocks,
        story_blocks=story_blocks,
        video_type=video_type,
    )
    try:
        chat = model or get_chat_model(temperature=0.35)
        structured = chat.with_structured_output(GeminiStoryboardBatch)
        result = structured.invoke(
            [
                SystemMessage(content=STORYBOARD_AGENT_SYSTEM),
                HumanMessage(content=user_prompt),
            ]
        )
    except ConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini storyboard generation failed")
        raise StoryboardAgentError(f"Gemini storyboard generation failed: {exc}") from exc

    if isinstance(result, GeminiStoryboardBatch):
        return result
    if isinstance(result, dict):
        return GeminiStoryboardBatch.model_validate(result)
    raise StoryboardAgentError("Unexpected Gemini storyboard structured output type.")
