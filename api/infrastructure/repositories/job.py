"""
infrastructure/repositories/job.py

Concrete PostgreSQL-backed job repository.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from domain.job.aggregate import STATUS_PUBLISHED, JobAggregate
from domain.job.exceptions import JobNotFoundError
from domain.job.repositories import JobRepository
from infrastructure.mappers.job import JobMapper
from infrastructure.models.job import JobRecord


class DjangoJobRepository(JobRepository):
    def get_by_id(self, job_id: str) -> JobAggregate:
        try:
            record = (
                JobRecord.objects
                .prefetch_related("required_skills")
                .get(job_id=job_id)
            )
        except (JobRecord.DoesNotExist, DjangoValidationError):
            raise JobNotFoundError(f"Job '{job_id}' not found")
        return JobMapper.to_aggregate(record)

    @transaction.atomic
    def save(self, job: JobAggregate) -> None:
        try:
            record = JobRecord.objects.get(job_id=job.job_id)
        except JobRecord.DoesNotExist:
            record = JobRecord(job_id=job.job_id)
        JobMapper.update_record(record, job)
        record.save()
        JobMapper.sync_related(record, job)

    def list_published(self) -> list[JobAggregate]:
        records = (
            JobRecord.objects
            .prefetch_related("required_skills")
            .filter(status=STATUS_PUBLISHED)
        )
        return [JobMapper.to_aggregate(r) for r in records]

    def list_by_recruiter(self, recruiter_id: str) -> list[JobAggregate]:
        records = (
            JobRecord.objects
            .prefetch_related("required_skills")
            .filter(recruiter_id=recruiter_id)
            .order_by("-created_at")
        )
        return [JobMapper.to_aggregate(r) for r in records]
