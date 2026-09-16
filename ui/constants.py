"""Select-option lists for the video creation configuration form."""

from __future__ import annotations

VIDEO_TYPES: list[str] = [
    "Reels",
    "Shorts",
    "Explainer",
    "Educational",
    "Talking Head",
    "Vlog",
    "Cinematic",
    "Storytelling",
    "Documentary",
    "Interview",
    "Podcast",
    "Reaction",
    "Review",
    "Unboxing",
    "Comparison",
    "News",
    "Motivational",
    "Faceless",
    "Screen Recording",
    "Animation",
    "Motion Graphics",
    "Whiteboard",
    "AI Avatar",
    "Kinetic Typography",
    "Montage",
    "B-Roll",
    "Before/After",
    "Case Study",
    "Testimonial",
    "Advertisement",
    "UGC",
    "Live Stream",
    "Gaming",
    "Travel",
    "Fitness",
    "Comedy",
    "Meme",
    "POV",
    "Day-in-the-Life",
    "Behind-the-Scenes",
]

VISUAL_STYLES: list[str] = [
    "Anime",
    "Manga",
    "Hand-Painted Animation",
    "Stylized 3D Animation",
    "Watercolor",
    "Oil Painting",
    "Storybook",
    "Hand-Drawn 2D",
    "Paper Cutout",
    "Claymation",
    "Low-Poly 3D",
    "Voxel",
    "Comic Book",
    "Sketch",
    "Chibi",
    "Cyberpunk",
    "Steampunk",
    "Dark Fantasy",
    "Fairy-Tale Fantasy",
    "Photorealistic",
    "Cinematic",
    "Surreal",
    "Vintage Film",
]

ENVIRONMENTS: list[str] = [
    "Enchanted Forest",
    "Magical Forest",
    "Ancient Forest",
    "Foggy Forest",
    "Moonlit Forest",
    "Fairy Forest",
    "Mushroom Fantasy Forest",
    "Fairy-Tale Forest",
    "Mountain Forest",
    "Rainy Forest",
    "Sunrise Forest",
    "Golden-Hour Forest",
    "Winter Forest",
    "Autumn Forest",
    "Fantasy Tropical Forest",
    "Cosmic Forest",
    "Fantasy Kingdom",
    "Dragon Fantasy",
    "Wildlife/Nature Forest",
    "Magical Wizard Forest",
]

COUNTRIES: list[str] = [
    "United States",
    "India",
    "United Kingdom",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "Brazil",
    "Japan",
    "South Korea",
    "Mexico",
    "United Arab Emirates",
    "Singapore",
    "South Africa",
    "Nigeria",
]

REGIONS: list[str] = [
    "Global",
    "North America",
    "Europe",
    "Asia",
    "MENA",
    "LatAm",
    "Africa",
    "Oceania",
    "Gujarat",
    "Maharashtra",
    "Tamil Nadu",
    "California",
    "Texas",
    "Kansai",
    "Scotland",
]

LANGUAGES: list[str] = [
    "English",
    "Spanish",
    "Hindi",
    "Gujarati",
    "Marathi",
    "Tamil",
    "Portuguese",
    "French",
    "German",
    "Japanese",
    "Korean",
    "Arabic",
]

AUDIENCES: list[str] = [
    "General",
    "Gen Z",
    "Professionals",
    "Kids",
    "Parents",
    "Creators",
]

VOICES: list[str] = [
    "Original Voice",
    "AI Voice",
    "Male",
    "Female",
    "Neutral",
    "English Neutral",
    "Hindi Female",
    "Spanish Male",
    "Energetic",
    "Calm",
    "Narrative",
]

MUSIC_OPTIONS: list[str] = [
    "Original Audio",
    "No Music",
    "Background Music",
    "Dramatic",
    "Cinematic",
    "Funny",
    "Energetic",
    "Emotional",
    "Educational",
]

CAPTION_STYLES: list[str] = [
    "Platform Safe",
    "Minimal",
    "Pop",
    "Kinetic",
    "High Contrast",
]

REFRAME_ASPECTS: list[str] = [
    "Auto",
    "9:16",
    "1:1",
    "4:5",
]

HUMOR_STYLES: list[str] = [
    "None",
    "Dry",
    "Slapstick",
    "Sarcastic",
    "Wholesome",
    "Cultural",
]

# Display label → VideoJobConfig.humor_adaptation value
HUMOR_ADAPTATION_OPTIONS: list[tuple[str, str]] = [
    ("No Humor Adaptation", "none"),
    ("Original Humor", "original"),
    ("Localized Humor", "localized"),
    ("Regional Humor", "regional"),
]

HUMOR_ADAPTATION_LABELS: list[str] = [label for label, _ in HUMOR_ADAPTATION_OPTIONS]
HUMOR_ADAPTATION_LABEL_TO_VALUE: dict[str, str] = {
    label: value for label, value in HUMOR_ADAPTATION_OPTIONS
}

PLATFORMS: list[str] = [
    "Instagram",
    "Instagram Reels",
    "Facebook",
    "YouTube",
    "YouTube Shorts",
    "TikTok",
    "X",
    "LinkedIn",
    "Pinterest",
    "Snapchat",
    "Reddit",
]

TARGET_CLIP_DURATIONS: list[int] = [15, 30, 45, 60, 90]

# (field_key, display_label) for FeatureFlags
FEATURE_TOGGLE_DEFS: list[tuple[str, str]] = [
    ("smart_clip_detection", "Smart Clip Detection"),
    ("viral_moments", "Viral Moments"),
    ("funny_moments", "Funny Moments"),
    ("emotional_moments", "Emotional Moments"),
    ("educational_moments", "Educational Moments"),
    ("surprise_moments", "Surprise Moments"),
    ("important_moments", "Important Moments"),
    ("reaction_moments", "Reaction Moments"),
    ("inspirational_moments", "Inspirational Moments"),
    ("cinematic_moments", "Cinematic Moments"),
    ("expert_insights", "Expert Insights"),
    ("best_quotes", "Best Quotes"),
    ("b_roll", "B-Roll"),
    ("captions", "Captions"),
    ("voice", "Voice"),
    ("music", "Music"),
    ("cultural_adaptation", "Cultural Adaptation"),
    ("regional_humor", "Regional Humor"),
    ("smart_reframing", "Smart Reframing"),
    ("platform_optimization", "Platform Optimization"),
    ("enable_research", "Research (Parallel Search)"),
]

SOURCE_OPTIONS: list[str] = [
    "YouTube URL",
    "Upload Video",
    "Text / Script",
]

SOURCE_LABEL_TO_TYPE: dict[str, str] = {
    "YouTube URL": "youtube",
    "Upload Video": "upload",
    "Text / Script": "script",
}

ALLOWED_UPLOAD_TYPES: list[str] = ["mp4", "mov", "avi", "mkv", "webm"]
