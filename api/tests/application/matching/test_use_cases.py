"""
tests/application/matching/test_use_cases.py

Unit tests for MatchResumeToJobUseCase with mocked repositories and real domain services.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from application.common.exceptions import NotFoundError, UnauthorizedError
from application.matching.dtos import MatchRequestCommand, MatchResultDTO
from application.matching.use_cases import MatchResumeToJobUseCase
from domain.common.value_objects import Skill
from domain.job.aggregate import JobAggregate
from domain.job.exceptions import JobNotFoundError
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
)
from domain.matching.services import ResumeJobMatchingService
from domain.resume.aggregate import ResumeAggregate
from domain.resume.exceptions import ResumeNotFoundError
from domain.resume.value_objects import ContactInfo, Experience, RawResumeContent


# ============================================================
# Helpers
# ============================================================

_RESUME_TEXT = "Senior Python engineer with 7 years Django and REST APIs experience. " * 3
_JOB_DESC = (
    "We need a Senior Python Engineer to architect backend systems, "
    "build scalable REST APIs, and mentor junior developers on best practices."
)
_PYTHON = Skill(name="Python", category="programming", proficiency_level="expert")
_DJANGO = Skill(name="Django", category="framework", proficiency_level="advanced")


def _make_resume(
    candidate_id: str = "c1",
    skills: list[Skill] | None = None,
    experience_months: int = 24,
) -> ResumeAggregate:
    r = ResumeAggregate(
        resume_id="r1",
        candidate_id=candidate_id,
        raw_text=RawResumeContent(text=_RESUME_TEXT),
        contact_info=ContactInfo(email="a@b.com", phone="+1-000", location="NYC"),
    )
    for s in (skills or []):
        r.add_skill(s)
    if experience_months > 0:
        r.add_experience(
            Experience(role="Engineer", company="Co", duration_months=experience_months, responsibilities=[])
        )
    return r


def _make_job(required_skills: list[Skill] | None = None, req_exp: int = 24) -> JobAggregate:
    job = JobAggregate(
        job_id="j1",
        recruiter_id="rec1",
        title=JobTitle(value="Python Engineer"),
        company=CompanyName(value="TechCorp"),
        description=JobDescription(text=_JOB_DESC),
        location=Location(city="NYC", country="USA"),
        employment_type=EmploymentType.FULL_TIME,
        required_experience_months=req_exp,
    )
    for s in (required_skills or []):
        job.add_required_skill(s)
    return job


def _make_use_case(resume: ResumeAggregate | None, job: JobAggregate | None):
    resume_repo = MagicMock()
    job_repo = MagicMock()

    if resume is not None:
        resume_repo.get_by_id.return_value = resume
    else:
        resume_repo.get_by_id.side_effect = ResumeNotFoundError("not found")

    if job is not None:
        job_repo.get_by_id.return_value = job
    else:
        job_repo.get_by_id.side_effect = JobNotFoundError("not found")

    service = ResumeJobMatchingService()
    return MatchResumeToJobUseCase(resume_repo, job_repo, service)


def _cmd(candidate_id: str = "c1") -> MatchRequestCommand:
    return MatchRequestCommand(resume_id="r1", candidate_id=candidate_id, job_id="j1")


# ============================================================
# Success scenarios
# ============================================================


class TestMatchResumeToJobUseCase:
    def test_returns_match_result_dto(self):
        resume = _make_resume(skills=[_PYTHON, _DJANGO], experience_months=24)
        job = _make_job(required_skills=[_PYTHON, _DJANGO], req_exp=24)
        uc = _make_use_case(resume, job)
        dto = uc.execute(_cmd())
        assert isinstance(dto, MatchResultDTO)
        assert dto.resume_id == "r1"
        assert dto.job_id == "j1"

    def test_perfect_match_score_is_100(self):
        resume = _make_resume(skills=[_PYTHON, _DJANGO], experience_months=24)
        job = _make_job(required_skills=[_PYTHON, _DJANGO], req_exp=24)
        dto = _make_use_case(resume, job).execute(_cmd())
        assert dto.score == 100
        assert dto.score_label == "strong"

    def test_poor_match_has_gaps(self):
        resume = _make_resume(skills=[], experience_months=0)
        job = _make_job(required_skills=[_PYTHON, _DJANGO], req_exp=24)
        dto = _make_use_case(resume, job).execute(_cmd())
        assert dto.score < 50
        assert len(dto.gaps) > 0

    def test_score_label_in_dto(self):
        resume = _make_resume(skills=[_PYTHON], experience_months=12)
        job = _make_job(required_skills=[_PYTHON], req_exp=12)
        dto = _make_use_case(resume, job).execute(_cmd())
        assert dto.score_label in ("poor", "weak", "acceptable", "strong")

    def test_match_id_nonempty(self):
        resume = _make_resume(skills=[_PYTHON])
        job = _make_job(required_skills=[_PYTHON])
        dto = _make_use_case(resume, job).execute(_cmd())
        assert dto.match_id and len(dto.match_id) > 0

    def test_suggestions_present_for_missing_skills(self):
        resume = _make_resume(skills=[])
        job = _make_job(required_skills=[_PYTHON])
        dto = _make_use_case(resume, job).execute(_cmd())
        assert len(dto.suggestions) > 0

    def test_gaps_contain_missing_skill_type(self):
        resume = _make_resume(skills=[])
        job = _make_job(required_skills=[_PYTHON])
        dto = _make_use_case(resume, job).execute(_cmd())
        gap_types = [g.gap_type for g in dto.gaps]
        assert "missing_skill" in gap_types


# ============================================================
# Error scenarios
# ============================================================


class TestMatchResumeToJobErrors:
    def test_raises_not_found_when_resume_missing(self):
        uc = _make_use_case(resume=None, job=_make_job())
        with pytest.raises(NotFoundError):
            uc.execute(_cmd())

    def test_raises_not_found_when_job_missing(self):
        resume = _make_resume()
        uc = _make_use_case(resume=resume, job=None)
        with pytest.raises(NotFoundError):
            uc.execute(_cmd())

    def test_raises_unauthorized_for_wrong_candidate(self):
        resume = _make_resume(candidate_id="c1")
        job = _make_job()
        uc = _make_use_case(resume, job)
        with pytest.raises(UnauthorizedError):
            uc.execute(_cmd(candidate_id="c-other"))

    def test_not_found_error_has_resource_info(self):
        uc = _make_use_case(resume=None, job=None)
        try:
            uc.execute(_cmd())
        except NotFoundError as e:
            assert "r1" in str(e)
