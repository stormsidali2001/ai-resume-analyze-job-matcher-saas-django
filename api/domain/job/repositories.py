"""
domain/job/repositories.py

Abstract repository interface for JobAggregate persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.job.aggregate import JobAggregate


class JobRepository(ABC):
    """Port (interface) for job persistence. Implementations in infrastructure."""

    @abstractmethod
    def get_by_id(self, job_id: str) -> JobAggregate:
        """
        Retrieve a job by its ID.
        Raises JobNotFoundError if not found.
        """

    @abstractmethod
    def save(self, job: JobAggregate) -> None:
        """Persist a new or updated job (upsert semantics)."""

    @abstractmethod
    def list_published(self) -> list[JobAggregate]:
        """Return all jobs currently in PUBLISHED status."""
