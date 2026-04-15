"""
domain/job/aggregate.py

JobAggregate — the consistency boundary for a recruiter's job posting.
Lifecycle: DRAFT → PUBLISHED → CLOSED.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from domain.common.value_objects import Skill
from domain.job.exceptions import (
    InvalidJobError,
    JobAlreadyClosedError,
    JobAlreadyPublishedError,
)
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
    SalaryRange,
)

STATUS_DRAFT: Final[str] = "DRAFT"
STATUS_PUBLISHED: Final[str] = "PUBLISHED"
STATUS_CLOSED: Final[str] = "CLOSED"
VALID_STATUSES: Final[frozenset[str]] = frozenset(
    {STATUS_DRAFT, STATUS_PUBLISHED, STATUS_CLOSED}
)


class JobAggregate:
    """
    Aggregate root for a recruiter's job posting.

    Identity: job_id (str)
    Invariants:
        - job_id and recruiter_id must be non-empty
        - Cannot publish without at least 1 required skill
        - Cannot close a DRAFT job
        - Cannot modify description once PUBLISHED
        - required_experience_months >= 0
    """

    def __init__(
        self,
        job_id: str,
        recruiter_id: str,
        title: JobTitle,
        company: CompanyName,
        description: JobDescription,
        location: Location,
        employment_type: EmploymentType,
        required_skills: list[Skill] | None = None,
        required_experience_months: int = 0,
        salary_range: SalaryRange | None = None,
        status: str = STATUS_DRAFT,
        created_at: datetime | None = None,
    ) -> None:
        if not job_id or not job_id.strip():
            raise InvalidJobError("JobAggregate.job_id must not be empty.")
        if not recruiter_id or not recruiter_id.strip():
            raise InvalidJobError("JobAggregate.recruiter_id must not be empty.")
        if status not in VALID_STATUSES:
            raise InvalidJobError(
                f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}."
            )
        if required_experience_months < 0:
            raise InvalidJobError(
                f"required_experience_months must be >= 0, "
                f"got {required_experience_months}."
            )

        self._job_id = job_id
        self._recruiter_id = recruiter_id
        self._title = title
        self._company = company
        self._description = description
        self._location = location
        self._employment_type = employment_type
        self._required_skills: list[Skill] = list(required_skills or [])
        self._required_experience_months = required_experience_months
        self._salary_range = salary_range
        self._status = status
        self._created_at = created_at or datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def job_id(self) -> str:
        return self._job_id

    @property
    def recruiter_id(self) -> str:
        return self._recruiter_id

    @property
    def title(self) -> JobTitle:
        return self._title

    @property
    def company(self) -> CompanyName:
        return self._company

    @property
    def description(self) -> JobDescription:
        return self._description

    @property
    def location(self) -> Location:
        return self._location

    @property
    def employment_type(self) -> EmploymentType:
        return self._employment_type

    @property
    def required_skills(self) -> list[Skill]:
        return list(self._required_skills)  # defensive copy

    @property
    def required_experience_months(self) -> int:
        return self._required_experience_months

    @property
    def salary_range(self) -> SalaryRange | None:
        return self._salary_range

    @property
    def status(self) -> str:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def is_published(self) -> bool:
        return self._status == STATUS_PUBLISHED

    @property
    def is_closed(self) -> bool:
        return self._status == STATUS_CLOSED

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    def add_required_skill(self, skill: Skill) -> None:
        """Add a required skill. Silently deduplicates by name+category."""
        self._assert_modifiable()
        for existing in self._required_skills:
            if existing.matches(skill):
                return  # idempotent — already present
        self._required_skills.append(skill)

    def update_description(self, description: JobDescription) -> None:
        """Update the job description. Only allowed while in DRAFT status."""
        if self._status != STATUS_DRAFT:
            raise InvalidJobError(
                "Job description can only be updated while the job is in DRAFT status."
            )
        self._description = description

    def publish(self) -> None:
        """
        Transition DRAFT → PUBLISHED after validating publishing requirements.
        Raises JobAlreadyPublishedError if already published.
        Raises JobAlreadyClosedError if already closed.
        Raises InvalidJobError if validation fails.
        """
        if self._status == STATUS_PUBLISHED:
            raise JobAlreadyPublishedError(
                f"Job '{self._job_id}' is already published."
            )
        if self._status == STATUS_CLOSED:
            raise JobAlreadyClosedError(
                f"Job '{self._job_id}' is closed and cannot be published."
            )
        self.validate_for_publishing()
        self._status = STATUS_PUBLISHED

    def close(self) -> None:
        """
        Transition PUBLISHED → CLOSED.
        Raises InvalidJobError if in DRAFT.
        Raises JobAlreadyClosedError if already closed.
        """
        if self._status == STATUS_DRAFT:
            raise InvalidJobError(
                "A DRAFT job cannot be closed. Publish it first."
            )
        if self._status == STATUS_CLOSED:
            raise JobAlreadyClosedError(
                f"Job '{self._job_id}' is already closed."
            )
        self._status = STATUS_CLOSED

    def validate_for_publishing(self) -> None:
        """
        Verify the job meets all requirements before going live.
        Raises InvalidJobError listing all violations.
        """
        errors: list[str] = []
        if not self._title.value.strip():
            errors.append("Job must have a non-empty title.")
        if not self._required_skills:
            errors.append("Job must have at least one required skill before publishing.")
        if not self._description.text.strip():
            errors.append("Job must have a non-empty description.")
        if errors:
            raise InvalidJobError(
                "Job failed publishing validation: " + "; ".join(errors)
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _assert_modifiable(self) -> None:
        if self._status == STATUS_CLOSED:
            raise JobAlreadyClosedError(
                f"Job '{self._job_id}' is closed and cannot be modified."
            )

    def __repr__(self) -> str:
        return (
            f"JobAggregate(id={self._job_id!r}, "
            f"title={self._title.value!r}, "
            f"status={self._status!r}, "
            f"required_skills={len(self._required_skills)})"
        )
