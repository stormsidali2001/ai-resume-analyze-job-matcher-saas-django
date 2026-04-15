"""
infrastructure/repositories/resume.py

Concrete PostgreSQL-backed resume repository.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from domain.resume.aggregate import ResumeAggregate
from domain.resume.exceptions import ResumeNotFoundError
from domain.resume.repositories import ResumeRepository
from infrastructure.mappers.resume import ResumeMapper
from infrastructure.models.resume import ResumeRecord


class DjangoResumeRepository(ResumeRepository):
    def get_by_id(self, resume_id: str) -> ResumeAggregate:
        try:
            record = (
                ResumeRecord.objects
                .prefetch_related("skills", "experiences", "education")
                .get(resume_id=resume_id)
            )
        except (ResumeRecord.DoesNotExist, DjangoValidationError):
            raise ResumeNotFoundError(f"Resume '{resume_id}' not found")
        return ResumeMapper.to_aggregate(record)

    @transaction.atomic
    def save(self, resume: ResumeAggregate) -> None:
        try:
            record = ResumeRecord.objects.get(resume_id=resume.resume_id)
        except ResumeRecord.DoesNotExist:
            record = ResumeRecord(resume_id=resume.resume_id)
        ResumeMapper.update_record(record, resume)
        record.save()
        ResumeMapper.sync_related(record, resume)

    def list_by_candidate(self, candidate_id: str) -> list[ResumeAggregate]:
        records = (
            ResumeRecord.objects
            .prefetch_related("skills", "experiences", "education")
            .filter(candidate_id=candidate_id)
        )
        return [ResumeMapper.to_aggregate(r) for r in records]
