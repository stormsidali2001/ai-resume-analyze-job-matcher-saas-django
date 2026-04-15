"""
tests/domain/resume/test_services.py

Unit tests for ResumeAnalysisService.
"""

import pytest

from domain.common.value_objects import Skill
from domain.resume.aggregate import ResumeAggregate
from domain.resume.services import ResumeAnalysisService
from domain.resume.value_objects import ContactInfo, RawResumeContent


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def service():
    return ResumeAnalysisService()


@pytest.fixture
def resume():
    return ResumeAggregate(
        resume_id="r1",
        candidate_id="c1",
        raw_text=RawResumeContent(
            text="Experienced Python developer with Django and PostgreSQL skills. "
            "Also familiar with Docker and Kubernetes for container orchestration."
        ),
        contact_info=ContactInfo(
            email="bob@example.com", phone="+1-555-9999", location="Remote"
        ),
    )


# ============================================================
# extract_skills_from_text
# ============================================================


class TestExtractSkillsFromText:
    def test_finds_exact_keyword(self, service):
        result = service.extract_skills_from_text(
            text="I have extensive Python experience.",
            known_skills=["Python"],
        )
        assert len(result) == 1
        assert result[0].name == "Python"

    def test_case_insensitive_match(self, service):
        result = service.extract_skills_from_text(
            text="Proficient in PYTHON and django.",
            known_skills=["Python", "Django"],
        )
        names = [s.name for s in result]
        assert "Python" in names
        assert "Django" in names

    def test_does_not_find_absent_skill(self, service):
        result = service.extract_skills_from_text(
            text="I only know Java.",
            known_skills=["Python"],
        )
        assert result == []

    def test_deduplicates_same_keyword_twice(self, service):
        result = service.extract_skills_from_text(
            text="Python is great. I use python daily.",
            known_skills=["Python", "Python"],
        )
        assert len(result) == 1

    def test_empty_text_returns_empty(self, service):
        assert service.extract_skills_from_text("", ["Python"]) == []

    def test_empty_known_skills_returns_empty(self, service):
        assert service.extract_skills_from_text("Python developer", []) == []

    def test_returns_skill_value_objects(self, service):
        result = service.extract_skills_from_text("Python developer", ["Python"])
        assert isinstance(result[0], Skill)

    def test_custom_category_and_proficiency(self, service):
        result = service.extract_skills_from_text(
            text="Python expert",
            known_skills=["Python"],
            category="backend",
            proficiency_level="expert",
        )
        assert result[0].category == "backend"
        assert result[0].proficiency_level == "expert"

    @pytest.mark.parametrize(
        "text,skills,expected_count",
        [
            ("Python Django REST API", ["Python", "Django", "React"], 2),
            ("Java Spring Boot microservices", ["Python", "Django"], 0),
            ("Python, Go, Rust, C++", ["Python", "Go", "Rust", "Java"], 3),
            ("Full stack developer", ["Python", "React", "Node"], 0),
        ],
    )
    def test_various_texts(self, service, text, skills, expected_count):
        result = service.extract_skills_from_text(text, skills)
        assert len(result) == expected_count

    def test_multiword_skill_detected(self, service):
        result = service.extract_skills_from_text(
            text="Experience with machine learning projects",
            known_skills=["machine learning"],
        )
        assert len(result) == 1

    def test_blank_keyword_in_list_is_skipped(self, service):
        result = service.extract_skills_from_text(
            text="Python developer",
            known_skills=["Python", "", "  "],
        )
        assert len(result) == 1


# ============================================================
# enrich_resume
# ============================================================


class TestEnrichResume:
    def test_adds_new_skills_to_resume(self, service, resume):
        skills = [
            Skill(name="Python", category="programming", proficiency_level="advanced"),
            Skill(name="Django", category="framework", proficiency_level="intermediate"),
        ]
        service.enrich_resume(resume, skills)
        assert len(resume.skills) == 2

    def test_silently_skips_duplicate_skills(self, service, resume):
        skill = Skill(name="Python", category="programming", proficiency_level="advanced")
        resume.add_skill(skill)
        service.enrich_resume(resume, [skill])
        assert len(resume.skills) == 1

    def test_partial_add_when_some_duplicate(self, service, resume):
        existing = Skill(name="Python", category="programming", proficiency_level="advanced")
        new_skill = Skill(name="Docker", category="devops", proficiency_level="intermediate")
        resume.add_skill(existing)
        service.enrich_resume(resume, [existing, new_skill])
        assert len(resume.skills) == 2

    def test_enrich_with_empty_list_is_noop(self, service, resume):
        service.enrich_resume(resume, [])
        assert resume.skills == []

    def test_enrich_end_to_end(self, service, resume):
        skills = service.extract_skills_from_text(
            text=resume.raw_text.text,
            known_skills=["Python", "Django", "PostgreSQL", "Docker", "Kubernetes"],
        )
        service.enrich_resume(resume, skills)
        names = [s.name for s in resume.skills]
        assert "Python" in names
        assert "Django" in names
