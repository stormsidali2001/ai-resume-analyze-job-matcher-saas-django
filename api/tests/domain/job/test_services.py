"""
tests/domain/job/test_services.py

Unit tests for JobValidationService.
"""

import pytest

from domain.common.value_objects import Skill
from domain.job.aggregate import JobAggregate
from domain.job.services import JobValidationService
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
    SalaryRange,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def service():
    return JobValidationService()


def _make_job(**overrides) -> JobAggregate:
    defaults = dict(
        job_id="j1",
        recruiter_id="r1",
        title=JobTitle(value="Python Engineer"),
        company=CompanyName(value="Acme"),
        description=JobDescription(
            text="We need a Python engineer to build scalable APIs using "
            "Django and FastAPI for our enterprise SaaS platform."
        ),
        location=Location(city="NYC", country="USA"),
        employment_type=EmploymentType.FULL_TIME,
        required_experience_months=24,
    )
    defaults.update(overrides)
    return JobAggregate(**defaults)


# ============================================================
# validate
# ============================================================


class TestJobValidationService:
    def test_valid_job_with_skill_returns_no_errors(self, service):
        job = _make_job()
        job.add_required_skill(Skill(name="Python", category="programming", proficiency_level="advanced"))
        errors = service.validate(job)
        assert errors == []

    def test_missing_required_skill_returns_error(self, service):
        job = _make_job()
        errors = service.validate(job)
        assert any("skill" in e.lower() for e in errors)

    def test_is_ready_to_publish_true_with_skills(self, service):
        job = _make_job()
        job.add_required_skill(Skill(name="Python", category="programming", proficiency_level="advanced"))
        assert service.is_ready_to_publish(job) is True

    def test_is_ready_to_publish_false_without_skills(self, service):
        job = _make_job()
        assert service.is_ready_to_publish(job) is False

    def test_multiple_issues_returns_multiple_errors(self, service):
        job = _make_job()
        errors = service.validate(job)
        assert len(errors) >= 1

    @pytest.mark.parametrize("experience_months", [0, 6, 12, 24, 60])
    def test_valid_experience_months_passes(self, service, experience_months):
        job = _make_job(required_experience_months=experience_months)
        job.add_required_skill(Skill(name="Python", category="programming", proficiency_level="advanced"))
        errors = service.validate(job)
        assert errors == []
