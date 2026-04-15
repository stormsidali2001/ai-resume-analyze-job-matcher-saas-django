"""
tests/infrastructure/test_resume_repository.py

Integration tests for DjangoResumeRepository — requires a real PostgreSQL database.
"""

from __future__ import annotations

import pytest

from domain.common.value_objects import Skill
from domain.resume.aggregate import ResumeAggregate
from domain.resume.exceptions import ResumeNotFoundError
from domain.resume.value_objects import ContactInfo, Education, Experience, RawResumeContent
from infrastructure.repositories.resume import DjangoResumeRepository

pytestmark = pytest.mark.django_db

_LONG_TEXT = "Senior Python engineer with extensive experience in distributed systems and APIs. " * 2
_CONTACT = ContactInfo(email="test@example.com", phone="+1-555-0100", location="NYC")

# Fixed UUIDs for deterministic tests
_RESUME_ID   = "00000000-0000-0000-0000-000000000001"
_CANDIDATE_ID = "00000000-0000-0000-0000-000000000010"
_RESUME_ID_A  = "00000000-0000-0000-0000-000000000002"
_RESUME_ID_B  = "00000000-0000-0000-0000-000000000003"
_RESUME_ID_C  = "00000000-0000-0000-0000-000000000004"
_CANDIDATE_X  = "00000000-0000-0000-0000-000000000020"
_CANDIDATE_Y  = "00000000-0000-0000-0000-000000000021"


def _make_resume(
    resume_id: str = _RESUME_ID,
    candidate_id: str = _CANDIDATE_ID,
) -> ResumeAggregate:
    return ResumeAggregate(
        resume_id=resume_id,
        candidate_id=candidate_id,
        raw_text=RawResumeContent(text=_LONG_TEXT),
        contact_info=_CONTACT,
    )


class TestDjangoResumeRepository:
    def test_save_and_get_by_id(self):
        repo = DjangoResumeRepository()
        resume = _make_resume()
        repo.save(resume)

        loaded = repo.get_by_id(_RESUME_ID)
        assert loaded.resume_id == _RESUME_ID
        assert loaded.candidate_id == _CANDIDATE_ID
        assert loaded.contact_info.email == "test@example.com"

    def test_get_by_id_raises_not_found(self):
        repo = DjangoResumeRepository()
        with pytest.raises(ResumeNotFoundError):
            repo.get_by_id("00000000-0000-0000-0000-000000000099")

    def test_skills_round_trip(self):
        repo = DjangoResumeRepository()
        resume = _make_resume()
        resume.add_skill(Skill(name="Python", category="programming", proficiency_level="expert"))
        resume.add_skill(Skill(name="Django", category="framework", proficiency_level="advanced"))
        repo.save(resume)

        loaded = repo.get_by_id(_RESUME_ID)
        skill_names = [s.name for s in loaded.skills]
        assert "Python" in skill_names
        assert "Django" in skill_names

    def test_experience_round_trip(self):
        repo = DjangoResumeRepository()
        resume = _make_resume()
        resume.add_experience(
            Experience(role="Engineer", company="Acme", duration_months=24, responsibilities=["built APIs"])
        )
        repo.save(resume)

        loaded = repo.get_by_id(_RESUME_ID)
        assert len(loaded.experiences) == 1
        assert loaded.experiences[0].role == "Engineer"
        assert loaded.experiences[0].duration_months == 24

    def test_education_round_trip(self):
        repo = DjangoResumeRepository()
        resume = _make_resume()
        resume.add_education(
            Education(degree="BSc Computer Science", institution="MIT", graduation_year=2018)
        )
        repo.save(resume)

        loaded = repo.get_by_id(_RESUME_ID)
        assert len(loaded.education) == 1
        assert loaded.education[0].degree == "BSc Computer Science"

    def test_save_is_idempotent(self):
        """Saving the same resume twice updates rather than duplicating."""
        repo = DjangoResumeRepository()
        resume = _make_resume()
        repo.save(resume)
        resume.add_skill(Skill(name="FastAPI", category="framework", proficiency_level="intermediate"))
        repo.save(resume)

        loaded = repo.get_by_id(_RESUME_ID)
        assert len(loaded.skills) == 1  # not 2 duplicates

    def test_list_by_candidate(self):
        repo = DjangoResumeRepository()
        r1 = _make_resume(resume_id=_RESUME_ID_A, candidate_id=_CANDIDATE_X)
        r2 = _make_resume(resume_id=_RESUME_ID_B, candidate_id=_CANDIDATE_X)
        other = _make_resume(resume_id=_RESUME_ID_C, candidate_id=_CANDIDATE_Y)
        repo.save(r1)
        repo.save(r2)
        repo.save(other)

        results = repo.list_by_candidate(_CANDIDATE_X)
        assert len(results) == 2
        assert all(r.candidate_id == _CANDIDATE_X for r in results)
