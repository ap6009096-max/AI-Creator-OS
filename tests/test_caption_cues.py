"""Tests for caption cue building — never invent timing."""

from __future__ import annotations

from tools.captions.cues import (
    build_localized_track,
    build_sentence_cues,
    build_word_cues,
    has_usable_timestamps,
)


SPEECH = {
    "language": "en",
    "segments": [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.0,
            "text": "Hello viral world",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "viral", "start": 0.5, "end": 1.2},
                {"word": "world", "start": 1.2, "end": 2.0},
            ],
        }
    ],
}


def test_word_and_sentence_cues_from_speech() -> None:
    words = build_word_cues(SPEECH)
    sentences = build_sentence_cues(SPEECH)
    assert len(words) == 3
    assert len(sentences) == 1
    assert sentences[0].start == 0.0
    assert sentences[0].end == 2.0
    assert "viral" in [t.lower() for t in sentences[0].highlighted_tokens]
    assert has_usable_timestamps(SPEECH) is True


def test_rejects_missing_timestamps() -> None:
    bad = {
        "segments": [
            {"text": "No times here", "words": [{"word": "No"}]},
        ]
    }
    assert build_word_cues(bad) == []
    assert build_sentence_cues(bad) == []
    assert has_usable_timestamps(bad) is False


def test_structured_fallback_only_when_timed() -> None:
    timed = {
        "sentences": [
            {"text": "Timed sentence", "start_seconds": 1.0, "end_seconds": 2.0},
            {"text": "Untimed", "start_seconds": None, "end_seconds": None},
        ]
    }
    cues = build_sentence_cues(None, timed)
    assert len(cues) == 1
    assert cues[0].text == "Timed sentence"


def test_never_invents_even_spacing() -> None:
    # Empty speech + untimed structured → no cues
    structured = {
        "sentences": [
            {"text": "A", "start_seconds": None, "end_seconds": None},
            {"text": "B"},
        ]
    }
    assert build_sentence_cues(None, structured) == []
    assert has_usable_timestamps(None, structured) is False


def test_emoji_flag() -> None:
    cues = build_sentence_cues(
        {
            "segments": [
                {"start": 0, "end": 1, "text": "I love this", "words": []},
            ]
        },
        emoji_enabled=True,
    )
    assert cues[0].emoji == "❤️"
    off = build_sentence_cues(
        {
            "segments": [
                {"start": 0, "end": 1, "text": "I love this", "words": []},
            ]
        },
        emoji_enabled=False,
    )
    assert off[0].emoji == ""


def test_localized_track_reuses_timings() -> None:
    sentences = build_sentence_cues(SPEECH)
    localizations = {
        "versions": [
            {
                "scripts": [
                    {"short_script": "Hola mundo viral"},
                ]
            }
        ]
    }
    track, note = build_localized_track(
        sentences,
        localizations,
        language="Spanish",
        direction="ltr",
    )
    assert track is not None
    assert track.localized is True
    assert track.cues[0].start == sentences[0].start
    assert track.cues[0].end == sentences[0].end
    assert track.cues[0].text == "Hola mundo viral"
    assert note
