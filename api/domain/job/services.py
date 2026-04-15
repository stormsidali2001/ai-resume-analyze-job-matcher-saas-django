"""
domain/job/services.py

Domain service for Job validation logic that spans concerns not
naturally owned by the JobAggregate itself.
"""

from __future__ import annotations

from domain.job.aggregate import JobAggregate, STATUS_DRAFT


class JobValidationService:
    """
    Stateless service that validates a JobAggregate against business rules
    and returns a human-readable list of error messages.

    Returning errors as a list (rather than raising immediately) lets the
    application layer accumulate all problems and surface them together
    in a single API response — better UX than fail-fast.
    """

    def validate(self, job: JobAggregate) -> list[str]:
        """
        Run all business validation checks on the job.

        Returns:
            An empty list if the job is valid, or a list of error
            message strings describing each violation found.
        """
        errors: list[str] = []

        if not job.title.value.strip():
            errors.append("Job title must not be empty.")

        if not job.company.value.strip():
            errors.append("Company name must not be empty.")

        if not job.required_skills:
            errors.append("Job must specify at least one required skill.")

        if job.required_experience_months < 0:
            errors.append("Required experience months must be non-negative.")

        if job.salary_range is not None:
            if job.salary_range.min_salary > job.salary_range.max_salary:
                errors.append(
                    "Salary range minimum must not exceed the maximum."
                )

        return errors

    def is_ready_to_publish(self, job: JobAggregate) -> bool:
        """Convenience predicate — True when validate() returns no errors."""
        return len(self.validate(job)) == 0
