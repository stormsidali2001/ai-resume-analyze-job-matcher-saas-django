"""
infrastructure/mappers/job.py

Bidirectional mapping between JobRecord (ORM) and JobAggregate (domain).
"""

from __future__ import annotations

from domain.common.value_objects import Skill
from domain.job.aggregate import JobAggregate
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
    SalaryRange,
)
from infrastructure.models.job import JobRecord, JobSkillRecord


class JobMapper:
    @staticmethod
    def to_aggregate(record: JobRecord) -> JobAggregate:
        """Hydrate a JobRecord (with prefetched relations) into a JobAggregate."""
        salary_range = None
        if record.salary_min is not None and record.salary_max is not None:
            salary_range = SalaryRange(
                min_salary=record.salary_min,
                max_salary=record.salary_max,
                currency=record.salary_currency,
            )

        job = JobAggregate(
            job_id=str(record.job_id),
            recruiter_id=str(record.recruiter_id),
            title=JobTitle(value=record.title),
            company=CompanyName(value=record.company),
            description=JobDescription(text=record.description),
            location=Location(
                city=record.location_city,
                country=record.location_country,
                remote=record.location_remote,
            ),
            employment_type=EmploymentType(record.employment_type),
            required_experience_months=record.required_experience_months,
            salary_range=salary_range,
        )
        # Restore internal state
        job._status = record.status
        job._created_at = record.created_at

        for skill_rec in record.required_skills.all():
            job.add_required_skill(
                Skill(
                    name=skill_rec.name,
                    category=skill_rec.category,
                    proficiency_level=skill_rec.proficiency_level,
                )
            )

        return job

    @staticmethod
    def update_record(record: JobRecord, job: JobAggregate) -> None:
        """Sync scalar fields from the aggregate onto the ORM record."""
        record.recruiter_id = job.recruiter_id
        record.title = job.title.value
        record.company = job.company.value
        record.description = job.description.text
        record.location_city = job.location.city
        record.location_country = job.location.country
        record.location_remote = job.location.remote
        record.employment_type = job.employment_type.value
        record.required_experience_months = job.required_experience_months
        record.status = job.status
        record.created_at = job.created_at

        if job.salary_range:
            record.salary_min = job.salary_range.min_salary
            record.salary_max = job.salary_range.max_salary
            record.salary_currency = job.salary_range.currency
        else:
            record.salary_min = None
            record.salary_max = None

    @staticmethod
    def sync_related(record: JobRecord, job: JobAggregate) -> None:
        """Delete-and-recreate required skill records."""
        record.required_skills.all().delete()
        JobSkillRecord.objects.bulk_create([
            JobSkillRecord(
                job=record,
                name=s.name,
                category=s.category,
                proficiency_level=s.proficiency_level,
            )
            for s in job.required_skills
        ])
