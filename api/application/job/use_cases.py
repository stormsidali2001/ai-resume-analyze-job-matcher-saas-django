"""
application/job/use_cases.py

Use cases for the Job bounded context.
"""

from __future__ import annotations

import uuid
from typing import Optional

from application.common.exceptions import NotFoundError, UnauthorizedError
from application.job.dtos import (
    AddSkillToJobCommand,
    CreateJobCommand,
    JobDTO,
    LocationDTO,
    SalaryRangeDTO,
    UpdateJobDescriptionCommand,
)
from domain.common.value_objects import Skill
from domain.job.aggregate import JobAggregate
from domain.job.exceptions import JobNotFoundError
from domain.job.repositories import JobRepository
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
    SalaryRange,
)


# ---------------------------------------------------------------------------
# Shared mapper
# ---------------------------------------------------------------------------


def _job_to_dto(job: JobAggregate) -> JobDTO:
    salary: Optional[SalaryRangeDTO] = None
    if job.salary_range is not None:
        salary = SalaryRangeDTO(
            min_salary=job.salary_range.min_salary,
            max_salary=job.salary_range.max_salary,
            currency=job.salary_range.currency,
        )

    from application.resume.dtos import SkillDTO  # local import avoids circular

    return JobDTO(
        job_id=job.job_id,
        recruiter_id=job.recruiter_id,
        title=job.title.value,
        company=job.company.value,
        description_preview=job.description.preview,
        required_skills=[
            SkillDTO(
                name=s.name,
                category=s.category,
                proficiency_level=s.proficiency_level,
            )
            for s in job.required_skills
        ],
        required_experience_months=job.required_experience_months,
        location=LocationDTO(
            city=job.location.city,
            country=job.location.country,
            remote=job.location.remote,
        ),
        employment_type=job.employment_type.value,
        salary_range=salary,
        status=job.status,
        created_at=job.created_at,
    )


def _fetch_and_authorize(
    repo: JobRepository,
    job_id: str,
    recruiter_id: str,
) -> JobAggregate:
    try:
        job = repo.get_by_id(job_id)
    except JobNotFoundError:
        raise NotFoundError("Job", job_id)
    if job.recruiter_id != recruiter_id:
        raise UnauthorizedError("Job", job_id)
    return job


def _fetch_public(repo: JobRepository, job_id: str) -> JobAggregate:
    try:
        return repo.get_by_id(job_id)
    except JobNotFoundError:
        raise NotFoundError("Job", job_id)


# ---------------------------------------------------------------------------
# Use Cases
# ---------------------------------------------------------------------------


class CreateJobUseCase:
    """Create a new job posting in DRAFT status."""

    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    def execute(self, cmd: CreateJobCommand) -> JobDTO:
        salary: Optional[SalaryRange] = None
        if cmd.salary_range is not None:
            salary = SalaryRange(
                min_salary=cmd.salary_range.min_salary,
                max_salary=cmd.salary_range.max_salary,
                currency=cmd.salary_range.currency,
            )

        job = JobAggregate(
            job_id=str(uuid.uuid4()),
            recruiter_id=cmd.recruiter_id,
            title=JobTitle(value=cmd.title),
            company=CompanyName(value=cmd.company),
            description=JobDescription(text=cmd.description),
            location=Location(city=cmd.city, country=cmd.country, remote=cmd.remote),
            employment_type=EmploymentType(cmd.employment_type),
            required_experience_months=cmd.required_experience_months,
            salary_range=salary,
        )
        self._repo.save(job)
        return _job_to_dto(job)


class GetJobUseCase:
    """Fetch a job by ID. Public — no ownership check."""

    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    def execute(self, job_id: str) -> JobDTO:
        job = _fetch_public(self._repo, job_id)
        return _job_to_dto(job)


class ListPublishedJobsUseCase:
    """Return all currently published jobs."""

    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    def execute(self) -> list[JobDTO]:
        jobs = self._repo.list_published()
        return [_job_to_dto(j) for j in jobs]


class PublishJobUseCase:
    """Transition a DRAFT job to PUBLISHED status."""

    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    def execute(self, job_id: str, requester_id: str) -> JobDTO:
        job = _fetch_and_authorize(self._repo, job_id, requester_id)
        job.publish()
        self._repo.save(job)
        return _job_to_dto(job)


class CloseJobUseCase:
    """Transition a PUBLISHED job to CLOSED status."""

    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    def execute(self, job_id: str, requester_id: str) -> JobDTO:
        job = _fetch_and_authorize(self._repo, job_id, requester_id)
        job.close()
        self._repo.save(job)
        return _job_to_dto(job)


class ListRecruiterJobsUseCase:
    """Return all jobs (any status) belonging to a recruiter."""

    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    def execute(self, recruiter_id: str) -> list[JobDTO]:
        jobs = self._repo.list_by_recruiter(recruiter_id)
        return [_job_to_dto(j) for j in jobs]


class AddRequiredSkillToJobUseCase:
    """Add a required skill to a job posting."""

    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    def execute(self, cmd: AddSkillToJobCommand) -> JobDTO:
        job = _fetch_and_authorize(self._repo, cmd.job_id, cmd.recruiter_id)
        skill = Skill(
            name=cmd.name,
            category=cmd.category,
            proficiency_level=cmd.proficiency_level,
        )
        job.add_required_skill(skill)
        self._repo.save(job)
        return _job_to_dto(job)
