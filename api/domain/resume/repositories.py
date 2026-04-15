"""
domain/resume/repositories.py

Abstract repository interface for ResumeAggregate persistence.
Concrete implementations live in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.resume.aggregate import ResumeAggregate


class ResumeRepository(ABC):
    """Port (interface) for resume persistence. Implementations in infrastructure."""

    @abstractmethod
    def get_by_id(self, resume_id: str) -> ResumeAggregate:
        """
        Retrieve a resume by its ID.
        Raises ResumeNotFoundError if not found.
        """

    @abstractmethod
    def save(self, resume: ResumeAggregate) -> None:
        """Persist a new or updated resume (upsert semantics)."""

    @abstractmethod
    def list_by_candidate(self, candidate_id: str) -> list[ResumeAggregate]:
        """Return all resumes belonging to the given candidate."""
