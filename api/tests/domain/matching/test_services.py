"""
tests/domain/matching/test_services.py

Unit tests for ResumeJobMatchingService.
"""

import pytest

from domain.common.value_objects import Skill
from domain.job.aggregate import JobAggregate
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
)
from domain.matching.aggregate import MatchResult
from domain.matching.services import ResumeJobMatchingService
from domain.resume.aggregate import ResumeAggregate
from domain.resume.value_objects import ContactInfo, Experience, RawResumeContent


# ============================================================
# Helpers
# ============================================================

_LONG_DESC = (
    "We are hiring a senior engineer to design, build, and maintain scalable "
    "backend systems using Python and Django. You will work closely with the "
    "product team and own end-to-end delivery of key platform features."
)


def _make_resume(
    skills: list[Skill],
    experience_months: int = 0,
) -> ResumeAggregate:
    r = ResumeAggregate(
        resume_id="r1",
        candidate_id="c1",
        raw_text=RawResumeContent(
            text="Python engineer with experience in Django and REST APIs. " * 3
        ),
        contact_info=ContactInfo(email="a@b.com", phone="+1-000", location="NYC"),
    )
    for s in skills:
        r.add_skill(s)
    if experience_months > 0:
        r.add_experience(
            Experience(
                role="Engineer",
                company="Acme",
                duration_months=experience_months,
                responsibilities=["built systems"],
            )
        )
    return r


def _make_job(
    required_skills: list[Skill],
    required_experience_months: int = 0,
) -> JobAggregate:
    job = JobAggregate(
        job_id="j1",
        recruiter_id="rec1",
        title=JobTitle(value="Python Engineer"),
        company=CompanyName(value="TechCorp"),
        description=JobDescription(text=_LONG_DESC),
        location=Location(city="NYC", country="USA"),
        employment_type=EmploymentType.FULL_TIME,
        required_experience_months=required_experience_months,
    )
    for s in required_skills:
        job.add_required_skill(s)
    return job


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def service():
    return ResumeJobMatchingService()


@pytest.fixture
def python_skill():
    return Skill(name="Python", category="programming", proficiency_level="expert")


@pytest.fixture
def django_skill():
    return Skill(name="Django", category="framework", proficiency_level="advanced")


@pytest.fixture
def react_skill():
    return Skill(name="React", category="frontend", proficiency_level="intermediate")


# ============================================================
# Perfect match
# ============================================================


class TestPerfectMatch:
    def test_all_skills_matched_full_experience(self, service, python_skill, django_skill):
        resume = _make_resume([python_skill, django_skill], experience_months=36)
        job = _make_job([python_skill, django_skill], required_experience_months=36)
        result = service.calculate_match(resume, job)
        assert isinstance(result, MatchResult)
        assert result.score.value == 100
        assert result.has_gaps is False
        assert result.suggestions == []

    def test_perfect_match_label_is_strong(self, service, python_skill):
        resume = _make_resume([python_skill], experience_months=12)
        job = _make_job([python_skill], required_experience_months=12)
        result = service.calculate_match(resume, job)
        assert result.score.label == "strong"


# ============================================================
# Partial match
# ============================================================


class TestPartialMatch:
    def test_half_skills_matched_produces_correct_score(
        self, service, python_skill, django_skill, react_skill
    ):
        resume = _make_resume([python_skill, django_skill], experience_months=24)
        job = _make_job([python_skill, django_skill, react_skill], required_experience_months=24)
        result = service.calculate_match(resume, job)
        # Skill: 2/3*60=40; Exp: 30; Base: 10 → 80
        assert result.score.value == 80
        assert len(result.gaps) == 1
        assert result.gaps[0].gap_type == "missing_skill"
        assert any("React" in s.text for s in result.suggestions)

    def test_experience_shortfall_creates_gap(self, service, python_skill):
        resume = _make_resume([python_skill], experience_months=12)
        job = _make_job([python_skill], required_experience_months=24)
        result = service.calculate_match(resume, job)
        # Skill: 60; Exp: 12/24*30=15; Base: 10 → 85
        assert result.score.value == 85
        exp_gaps = [g for g in result.gaps if g.gap_type == "experience_shortfall"]
        assert len(exp_gaps) == 1

    def test_experience_shortfall_suggestion_is_medium_priority(self, service, python_skill):
        resume = _make_resume([python_skill], experience_months=6)
        job = _make_job([python_skill], required_experience_months=24)
        result = service.calculate_match(resume, job)
        exp_suggestions = [s for s in result.suggestions if s.category == "experience"]
        assert all(s.priority == "medium" for s in exp_suggestions)


# ============================================================
# Poor match
# ============================================================


class TestPoorMatch:
    def test_no_skills_no_experience(self, service, python_skill, django_skill):
        resume = _make_resume(skills=[], experience_months=0)
        job = _make_job([python_skill, django_skill], required_experience_months=24)
        result = service.calculate_match(resume, job)
        # Skill: 0; Exp: 0; Base: 10 → 10
        assert result.score.value == 10
        assert result.score.label == "poor"
        assert len(result.gaps) == 3  # 2 skill + 1 experience

    def test_missing_skills_generate_high_priority_suggestions(self, service, python_skill):
        resume = _make_resume(skills=[])
        job = _make_job([python_skill])
        result = service.calculate_match(resume, job)
        assert all(s.priority == "high" for s in result.suggestions)


# ============================================================
# Edge cases
# ============================================================


class TestEdgeCases:
    def test_no_required_skills_gives_full_skill_score(self, service, python_skill):
        resume = _make_resume([python_skill], experience_months=12)
        job = _make_job(required_skills=[], required_experience_months=12)
        result = service.calculate_match(resume, job)
        assert result.score.value == 100

    def test_no_required_experience_gives_full_exp_score(self, service, python_skill):
        resume = _make_resume([python_skill], experience_months=0)
        job = _make_job([python_skill], required_experience_months=0)
        result = service.calculate_match(resume, job)
        assert result.score.value == 100

    def test_excess_experience_capped_at_max(self, service, python_skill):
        resume = _make_resume([python_skill], experience_months=120)
        job = _make_job([python_skill], required_experience_months=24)
        result = service.calculate_match(resume, job)
        assert result.score.value == 100

    def test_score_never_exceeds_100(self, service, python_skill, django_skill):
        resume = _make_resume([python_skill, django_skill], experience_months=999)
        job = _make_job([python_skill], required_experience_months=1)
        result = service.calculate_match(resume, job)
        assert result.score.value <= 100

    def test_score_never_below_zero(self, service, python_skill):
        resume = _make_resume(skills=[])
        job = _make_job([python_skill], required_experience_months=0)
        result = service.calculate_match(resume, job)
        assert result.score.value >= 0

    def test_custom_match_id_is_used(self, service, python_skill):
        resume = _make_resume([python_skill])
        job = _make_job([python_skill])
        result = service.calculate_match(resume, job, match_id="custom-id-123")
        assert result.match_id == "custom-id-123"

    def test_auto_generated_match_id_is_nonempty(self, service, python_skill):
        resume = _make_resume([python_skill])
        job = _make_job([python_skill])
        result = service.calculate_match(resume, job)
        assert result.match_id and len(result.match_id) > 0

    def test_resume_and_job_ids_preserved(self, service, python_skill):
        resume = _make_resume([python_skill])
        job = _make_job([python_skill])
        result = service.calculate_match(resume, job)
        assert result.resume_id == resume.resume_id
        assert result.job_id == job.job_id

    @pytest.mark.parametrize(
        "matched,total,exp_months,req_exp,check",
        [
            (2, 2, 12, 12, lambda s: s == 100),
            (0, 2, 0, 12, lambda s: s < 70),
            (1, 2, 12, 12, lambda s: s == 70),
        ],
    )
    def test_scoring_formula_parametrize(self, service, matched, total, exp_months, req_exp, check):
        all_skills = [
            Skill(name=f"Skill{i}", category="cat", proficiency_level="intermediate")
            for i in range(total)
        ]
        resume = _make_resume(all_skills[:matched], experience_months=exp_months)
        job = _make_job(all_skills, required_experience_months=req_exp)
        result = service.calculate_match(resume, job)
        assert check(result.score.value)
