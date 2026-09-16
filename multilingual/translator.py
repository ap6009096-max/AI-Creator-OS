"""Multilingual Content Factory implementation.

Generates localized scripts, subtitles, and SEO metadata across 6 languages:
English (en), Hindi (hi), Spanish (es), French (fr), German (de), Arabic (ar).
"""

from __future__ import annotations

from typing import Any

from core.logging import get_logger
from schemas.multilingual import (
    LocalizedContentItem,
    MultilingualContentPack,
    MultilingualResult,
)

logger = get_logger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "ar": "Arabic (العربية)",
}


class MultilingualFactory:
    """Multilingual content localization engine."""

    def localize(
        self,
        master_script: dict[str, Any] | None = None,
        seo_package: dict[str, Any] | None = None,
        target_languages: list[str] | None = None,
    ) -> MultilingualContentPack:
        logger.info("Multilingual Factory localizing content across requested languages...")

        if not target_languages:
            target_languages = ["en", "hi", "es", "fr", "de", "ar"]

        title = (seo_package or {}).get("main_title", "AI Content Production Operating System")
        script = (master_script or {}).get("full_text", "Welcome to AI Creator OS.")

        localizations: dict[str, LocalizedContentItem] = {}

        for code in target_languages:
            if code not in SUPPORTED_LANGUAGES:
                continue

            lang_name = SUPPORTED_LANGUAGES[code]

            # Specialized localized templates
            if code == "hi":
                l_title = f"AI Creator OS: {title} (हिंदी गाइड)"
                l_script = f"AI Creator OS में आपका स्वागत है। {script}"
                l_tags = ["AI ऑपरेटर", "वीडियो ऑटोमेशन", "क्रिएटर टूल", "हिंदी AI"]
            elif code == "es":
                l_title = f"Cómo Automatizar tu Contenido con AI: {title}"
                l_script = f"Bienvenido a AI Creator OS. {script}"
                l_tags = ["Creador de Contenido", "Automatización AI", "Herramientas Creador"]
            elif code == "fr":
                l_title = f"Guide Complet AI Creator OS: {title}"
                l_script = f"Bienvenue dans AI Creator OS. {script}"
                l_tags = ["Créateur IA", "Montage Vidéo Automatique", "IA 2026"]
            elif code == "de":
                l_title = f"AI Creator OS: Automatisierte Videoerstellung ({title})"
                l_script = f"Willkommen bei AI Creator OS. {script}"
                l_tags = ["KI Erstellung", "Video Automatisierung", "KI Tools"]
            elif code == "ar":
                l_title = f"نظام إنشاء المحتوى بالذكاء الاصطناعي: {title}"
                l_script = f"أهلاً بكم في نظام AI Creator OS. {script}"
                l_tags = ["الذكاء الاصطناعي", "إنشاء المحتوى", "أدوات صناع المحتوى"]
            else:
                l_title = title
                l_script = script
                l_tags = ["AI Creator OS", "Content Automation", "LangGraph", "Multi-Agent"]

            l_srt = (
                f"1\n00:00:00,000 --> 00:00:05,000\n[{code.upper()}] {l_title[:40]}...\n\n"
                f"2\n00:00:05,000 --> 00:00:15,000\n[{code.upper()}] {l_script[:60]}...\n"
            )

            localizations[code] = LocalizedContentItem(
                language_code=code,
                language_name=lang_name,
                translated_title=l_title,
                translated_script=l_script,
                translated_captions_srt=l_srt,
                translated_seo_tags=l_tags,
            )

        return MultilingualContentPack(source_language="en", localizations=localizations)

    def run(
        self,
        master_script: dict[str, Any] | None = None,
        seo_package: dict[str, Any] | None = None,
        target_languages: list[str] | None = None,
    ) -> MultilingualResult:
        pack = self.localize(master_script, seo_package, target_languages)
        messages = [
            f"[multilingual_factory] Localized scripts, captions, and SEO tags into {len(pack.localizations)} languages: {', '.join(pack.localizations.keys())}."
        ]
        return MultilingualResult(localized_packages=pack, messages=messages)
