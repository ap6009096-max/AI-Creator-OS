"""Tests for AI Creator OS upgraded feature suites."""

from __future__ import annotations

from content_calendar.planner import SmartContentPlanner
from dashboard.metrics_calculator import CreatorDashboardCalculator
from employees.director import AIDirector
from employees.editor import AIEditor
from employees.researcher import AIResearcher
from employees.script_writer import AIScriptWriter
from employees.seo_manager import AISEOManager
from employees.social_manager import AISocialMediaManager
from employees.strategist import AIStrategist
from intelligence.viral_engine import ViralIntelligenceEngine
from memory.manager import CreatorMemoryManager
from multilingual.translator import MultilingualFactory
from qa.evaluator import AIQualityAssuranceAgent
from repurposing.engine import ContentRepurposingEngine


def test_creator_memory_system(tmp_path):
    """Test saving and loading creator memory profiles."""
    mgr = CreatorMemoryManager(storage_dir=tmp_path)
    profile = mgr.load_profile("test_creator")
    assert profile.creator_id == "test_creator"

    profile.channel_name = "Tech AI Master"
    mgr.save_profile(profile)

    loaded = mgr.load_profile("test_creator")
    assert loaded.channel_name == "Tech AI Master"


def test_viral_content_intelligence():
    """Test viral hook generation and score prediction."""
    engine = ViralIntelligenceEngine()
    pack = engine.analyze("Building AI Agents in 2026")
    assert len(pack.viral_hooks) == 5
    assert pack.predicted_engagement_score >= 70.0
    assert pack.predicted_retention_score >= 70.0
    assert len(pack.pre_generation_recommendations) > 0


def test_ai_employee_team():
    """Test all 7 AI Employee team nodes."""
    researcher = AIResearcher().run(topic="AI Video Automation")
    assert "research_brief" in researcher

    strategist = AIStrategist().run(research_brief=researcher["research_brief"])
    assert "content_strategy" in strategist

    script_writer = AIScriptWriter().run(
        content_strategy=strategist["content_strategy"],
        research_brief=researcher["research_brief"],
    )
    assert "master_script" in script_writer

    director = AIDirector().run(master_script=script_writer["master_script"])
    assert "director_storyboard" in director

    editor = AIEditor().run(director_storyboard=director["director_storyboard"])
    assert "rendered_assets" in editor

    seo = AISEOManager().run(master_script=script_writer["master_script"])
    assert "seo_package" in seo

    social = AISocialMediaManager().run(master_script=script_writer["master_script"])
    assert "social_media_pack" in social


def test_content_repurposing_engine():
    """Test multi-channel asset generation."""
    engine = ContentRepurposingEngine()
    pkg = engine.generate_package(
        project_id="p123",
        master_script={"title": "Mastering LangGraph", "full_text": "Full script text for AI Video OS."},
    )
    assert pkg.project_id == "p123"
    assert len(pkg.shorts_clips) == 3
    assert len(pkg.blog_article_md) > 50
    assert "00:00:00" in pkg.captions_srt


def test_ai_quality_assurance_agent():
    """Test 100-point rubric evaluation."""
    qa = AIQualityAssuranceAgent()
    report = qa.evaluate(
        master_script={"full_text": "High quality script text with clear articulation."},
        seo_package={"main_title": "Automating Video Production with AI Employee Teams"},
    )
    assert report.overall_score >= 80.0
    assert report.breakdown.grammar_score == 20.0
    assert report.breakdown.copyright_risk_score == 20.0


def test_creator_dashboard_calculator(tmp_path):
    """Test ROI and savings calculations."""
    calc = CreatorDashboardCalculator(projects_dir=tmp_path)
    metrics = calc.calculate_metrics()
    assert metrics.hours_saved >= 8.5
    assert metrics.cost_saved_usd >= 350.0


def test_smart_content_calendar():
    """Test 7/30/90 day publishing schedule generation."""
    planner = SmartContentPlanner()
    pack = planner.plan(niche="AI Tools", goal="Audience Growth")
    assert len(pack.plan_7_day.items) == 7
    assert len(pack.plan_30_day.items) == 8
    assert len(pack.plan_90_day.items) == 3


def test_multilingual_content_factory():
    """Test localization across 6 languages."""
    factory = MultilingualFactory()
    pack = factory.localize(
        master_script={"full_text": "Hello world from AI OS."},
        seo_package={"main_title": "AI Content Automation"},
        target_languages=["en", "hi", "es", "fr", "de", "ar"],
    )
    assert len(pack.localizations) == 6
    assert "hi" in pack.localizations
    assert pack.localizations["hi"].language_name.startswith("Hindi")
