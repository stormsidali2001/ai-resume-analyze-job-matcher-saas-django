"""
tests/infrastructure/test_job_repository.py

Integration tests for DjangoJobRepository — requires a real PostgreSQL database.
"""

from __future__ import annotations

import pytest

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
from infrastructure.repositories.job import DjangoJobRepository

pytestmark = pytest.mark.django_db

_DESC = (
    "We are looking for a Senior Python Engineer to lead backend development, "
    "design REST APIs, and mentor the team. Strong Django skills required." * 2
)

# Fixed UUIDs for deterministic tests
_JOB_ID      = "00000000-0000-0000-0000-000000000001"
_JOB_DRAFT   = "00000000-0000-0000-0000-000000000002"
_JOB_PUB     = "00000000-0000-0000-0000-000000000003"
_RECRUITER_ID = "00000000-0000-0000-0000-000000000010"


def _make_job(
    job_id: str = _JOB_ID,
    recruiter_id: str = _RECRUITER_ID,
) -> JobAggregate:
    return JobAggregate(
        job_id=job_id,
        recruiter_id=recruiter_id,
        title=JobTitle(value="Python Engineer"),
        company=CompanyName(value="TechCorp"),
        description=JobDescription(text=_DESC),
        location=Location(city="NYC", country="USA"),
        employment_type=EmploymentType.FULL_TIME,
        required_experience_months=24,
    )


class TestDjangoJobRepository:
    def test_save_and_get_by_id(self):
        repo = DjangoJobRepository()
        job = _make_job()
        repo.save(job)

        loaded = repo.get_by_id(_JOB_ID)
        assert loaded.job_id == _JOB_ID
        assert loaded.recruiter_id == _RECRUITER_ID
        assert loaded.title.value == "Python Engineer"

    def test_get_by_id_raises_not_found(self):
        repo = DjangoJobRepository()
        with pytest.raises(JobNotFoundError):
            repo.get_by_id("00000000-0000-0000-0000-000000000099")

    def test_skills_round_trip(self):
        repo = DjangoJobRepository()
        job = _make_job()
        job.add_required_skill(Skill(name="Python", category="programming", proficiency_level="expert"))
        job.add_required_skill(Skill(name="Django", category="framework", proficiency_level="advanced"))
        repo.save(job)

        loaded = repo.get_by_id(_JOB_ID)
        skill_names = [s.name for s in loaded.required_skills]
        assert "Python" in skill_names
        assert "Django" in skill_names

    def test_list_published_returns_only_published(self):
        repo = DjangoJobRepository()
        job_draft = _make_job(job_id=_JOB_DRAFT)
        job_pub = _make_job(job_id=_JOB_PUB)
        job_pub.add_required_skill(Skill(name="Python", category="programming", proficiency_level="expert"))
        job_pub.publish()

        repo.save(job_draft)
        repo.save(job_pub)

        published = repo.list_published()
        ids = [j.job_id for j in published]
        assert _JOB_PUB in ids
        assert _JOB_DRAFT not in ids

    def test_save_is_idempotent(self):
        repo = DjangoJobRepository()
        job = _make_job()
        repo.save(job)
        job.add_required_skill(Skill(name="FastAPI", category="framework", proficiency_level="intermediate"))
        repo.save(job)

        loaded = repo.get_by_id(_JOB_ID)
        assert len(loaded.required_skills) == 1

    def test_location_round_trip(self):
        repo = DjangoJobRepository()
        job = _make_job()
        repo.save(job)

        loaded = repo.get_by_id(_JOB_ID)
        assert loaded.location.city == "NYC"
        assert loaded.location.country == "USA"
