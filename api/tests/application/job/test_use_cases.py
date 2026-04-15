"""
tests/application/job/test_use_cases.py

Unit tests for job use cases with mocked repositories.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from application.common.exceptions import NotFoundError, UnauthorizedError
from application.job.dtos import AddSkillToJobCommand, CreateJobCommand
from application.job.use_cases import (
    AddRequiredSkillToJobUseCase,
    CloseJobUseCase,
    CreateJobUseCase,
    GetJobUseCase,
    ListPublishedJobsUseCase,
    PublishJobUseCase,
)
from domain.job.aggregate import STATUS_CLOSED, STATUS_PUBLISHED, JobAggregate
from domain.job.exceptions import InvalidJobError, JobNotFoundError
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
)


# ============================================================
# Helpers
# ============================================================

_DESC = (
    "We are hiring a Senior Python Engineer to lead backend development. "
    "You will design and build scalable REST APIs. Strong Python expertise required."
)


def _make_job(
    job_id: str = "j1",
    recruiter_id: str = "rec1",
    with_skill: bool = False,
) -> JobAggregate:
    job = JobAggregate(
        job_id=job_id,
        recruiter_id=recruiter_id,
        title=JobTitle(value="Python Engineer"),
        company=CompanyName(value="TechCorp"),
        description=JobDescription(text=_DESC),
        location=Location(city="NYC", country="USA"),
        employment_type=EmploymentType.FULL_TIME,
    )
    if with_skill:
        from domain.common.value_objects import Skill
        job.add_required_skill(Skill(name="Python", category="programming", proficiency_level="expert"))
    return job


def _mock_repo(job: JobAggregate | None = None, published: list[JobAggregate] | None = None):
    repo = MagicMock()
    if job is not None:
        repo.get_by_id.return_value = job
    else:
        repo.get_by_id.side_effect = JobNotFoundError("not found")
    repo.list_published.return_value = published or []
    return repo


def _create_cmd(**overrides) -> CreateJobCommand:
    defaults = dict(
        recruiter_id="rec1",
        title="Python Engineer",
        company="TechCorp",
        description=_DESC,
        city="NYC",
        country="USA",
        employment_type="full_time",
        required_experience_months=24,
    )
    defaults.update(overrides)
    return CreateJobCommand(**defaults)


# ============================================================
# CreateJobUseCase
# ============================================================


class TestCreateJobUseCase:
    def test_creates_draft_job(self):
        repo = MagicMock()
        dto = CreateJobUseCase(repo).execute(_create_cmd())
        assert dto.status == "DRAFT"
        assert dto.recruiter_id == "rec1"

    def test_repo_save_called_once(self):
        repo = MagicMock()
        CreateJobUseCase(repo).execute(_create_cmd())
        repo.save.assert_called_once()

    def test_generated_job_id_nonempty(self):
        repo = MagicMock()
        dto = CreateJobUseCase(repo).execute(_create_cmd())
        assert dto.job_id and len(dto.job_id) > 0

    def test_employment_type_in_dto(self):
        repo = MagicMock()
        dto = CreateJobUseCase(repo).execute(_create_cmd(employment_type="contract"))
        assert dto.employment_type == "contract"

    def test_salary_range_included_when_provided(self):
        from application.job.dtos import SalaryRangeDTO
        repo = MagicMock()
        cmd = _create_cmd(salary_range=SalaryRangeDTO(min_salary=80_000, max_salary=120_000))
        dto = CreateJobUseCase(repo).execute(cmd)
        assert dto.salary_range is not None
        assert dto.salary_range.min_salary == 80_000

    def test_salary_range_none_when_not_provided(self):
        repo = MagicMock()
        dto = CreateJobUseCase(repo).execute(_create_cmd())
        assert dto.salary_range is None


# ============================================================
# GetJobUseCase
# ============================================================


class TestGetJobUseCase:
    def test_returns_job_dto(self):
        job = _make_job()
        repo = _mock_repo(job)
        dto = GetJobUseCase(repo).execute("j1")
        assert dto.job_id == "j1"

    def test_raises_not_found(self):
        repo = _mock_repo(None)
        with pytest.raises(NotFoundError):
            GetJobUseCase(repo).execute("missing")

    def test_no_ownership_check(self):
        """Anyone can view a job — no recruiter_id required."""
        job = _make_job(recruiter_id="rec-owner")
        repo = _mock_repo(job)
        dto = GetJobUseCase(repo).execute("j1")
        assert dto.recruiter_id == "rec-owner"

    def test_repo_save_never_called(self):
        job = _make_job()
        repo = _mock_repo(job)
        GetJobUseCase(repo).execute("j1")
        repo.save.assert_not_called()


# ============================================================
# ListPublishedJobsUseCase
# ============================================================


class TestListPublishedJobsUseCase:
    def test_returns_published_jobs(self):
        job = _make_job(with_skill=True)
        job.publish()
        repo = _mock_repo(published=[job])
        dtos = ListPublishedJobsUseCase(repo).execute()
        assert len(dtos) == 1

    def test_returns_empty_when_none(self):
        repo = _mock_repo(published=[])
        assert ListPublishedJobsUseCase(repo).execute() == []

    def test_repo_save_never_called(self):
        repo = MagicMock()
        repo.list_published.return_value = []
        ListPublishedJobsUseCase(repo).execute()
        repo.save.assert_not_called()


# ============================================================
# PublishJobUseCase
# ============================================================


class TestPublishJobUseCase:
    def test_publishes_job(self):
        job = _make_job(with_skill=True)
        repo = _mock_repo(job)
        dto = PublishJobUseCase(repo).execute("j1", "rec1")
        assert dto.status == STATUS_PUBLISHED

    def test_repo_save_called(self):
        job = _make_job(with_skill=True)
        repo = _mock_repo(job)
        PublishJobUseCase(repo).execute("j1", "rec1")
        repo.save.assert_called_once()

    def test_raises_not_found(self):
        repo = _mock_repo(None)
        with pytest.raises(NotFoundError):
            PublishJobUseCase(repo).execute("missing", "rec1")

    def test_raises_unauthorized(self):
        job = _make_job(recruiter_id="rec1")
        repo = _mock_repo(job)
        with pytest.raises(UnauthorizedError):
            PublishJobUseCase(repo).execute("j1", "other-recruiter")

    def test_raises_domain_error_when_no_skills(self):
        job = _make_job(with_skill=False)  # no skills → cannot publish
        repo = _mock_repo(job)
        with pytest.raises(InvalidJobError):
            PublishJobUseCase(repo).execute("j1", "rec1")


# ============================================================
# CloseJobUseCase
# ============================================================


class TestCloseJobUseCase:
    def test_closes_published_job(self):
        job = _make_job(with_skill=True)
        job.publish()
        repo = _mock_repo(job)
        dto = CloseJobUseCase(repo).execute("j1", "rec1")
        assert dto.status == STATUS_CLOSED

    def test_repo_save_called(self):
        job = _make_job(with_skill=True)
        job.publish()
        repo = _mock_repo(job)
        CloseJobUseCase(repo).execute("j1", "rec1")
        repo.save.assert_called_once()

    def test_raises_unauthorized(self):
        job = _make_job(with_skill=True, recruiter_id="rec1")
        job.publish()
        repo = _mock_repo(job)
        with pytest.raises(UnauthorizedError):
            CloseJobUseCase(repo).execute("j1", "wrong")

    def test_raises_not_found(self):
        repo = _mock_repo(None)
        with pytest.raises(NotFoundError):
            CloseJobUseCase(repo).execute("missing", "rec1")


# ============================================================
# AddRequiredSkillToJobUseCase
# ============================================================


class TestAddRequiredSkillToJobUseCase:
    def _cmd(self, **overrides):
        defaults = dict(
            job_id="j1",
            recruiter_id="rec1",
            name="Django",
            category="framework",
            proficiency_level="advanced",
        )
        defaults.update(overrides)
        return AddSkillToJobCommand(**defaults)

    def test_adds_skill_to_job(self):
        job = _make_job()
        repo = _mock_repo(job)
        dto = AddRequiredSkillToJobUseCase(repo).execute(self._cmd())
        assert any(s.name == "Django" for s in dto.required_skills)

    def test_repo_save_called(self):
        job = _make_job()
        repo = _mock_repo(job)
        AddRequiredSkillToJobUseCase(repo).execute(self._cmd())
        repo.save.assert_called_once()

    def test_raises_not_found(self):
        repo = _mock_repo(None)
        with pytest.raises(NotFoundError):
            AddRequiredSkillToJobUseCase(repo).execute(self._cmd())

    def test_raises_unauthorized(self):
        job = _make_job(recruiter_id="rec1")
        repo = _mock_repo(job)
        with pytest.raises(UnauthorizedError):
            AddRequiredSkillToJobUseCase(repo).execute(self._cmd(recruiter_id="other"))
