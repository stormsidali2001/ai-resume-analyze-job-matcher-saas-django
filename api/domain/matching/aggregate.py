"""
domain/matching/aggregate.py

MatchResult — an immutable aggregate capturing the outcome of comparing
a resume against a job posting. Created once by the matching service;
never mutated after creation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Final

from domain.common.value_objects import Gap, ImprovementSuggestion, MatchScore

_SENTINEL = object()


class MatchResult:
    """
    Aggregate root for a single resume–job match calculation.

    Identity: match_id (str)

    Immutable after construction — all fields are exposed as read-only
    properties. Use the MatchResult.create() factory to construct instances
    so that invariants are always validated.
    """

    def __init__(
        self,
        match_id: str,
        resume_id: str,
        job_id: str,
        score: MatchScore,
        gaps: list[Gap],
        suggestions: list[ImprovementSuggestion],
        calculated_at: datetime | None = None,
    ) -> None:
        if not match_id or not match_id.strip():
            raise ValueError("MatchResult.match_id must not be empty.")
        if not resume_id or not resume_id.strip():
            raise ValueError("MatchResult.resume_id must not be empty.")
        if not job_id or not job_id.strip():
            raise ValueError("MatchResult.job_id must not be empty.")

        self._match_id = match_id
        self._resume_id = resume_id
        self._job_id = job_id
        self._score = score
        self._gaps: tuple[Gap, ...] = tuple(gaps)
        self._suggestions: tuple[ImprovementSuggestion, ...] = tuple(suggestions)
        self._calculated_at = calculated_at or datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        match_id: str,
        resume_id: str,
        job_id: str,
        score: MatchScore,
        gaps: list[Gap],
        suggestions: list[ImprovementSuggestion],
    ) -> "MatchResult":
        """
        Preferred construction path. Validates all inputs and returns
        a fully-formed, immutable MatchResult.
        """
        return cls(
            match_id=match_id,
            resume_id=resume_id,
            job_id=job_id,
            score=score,
            gaps=gaps,
            suggestions=suggestions,
        )

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def match_id(self) -> str:
        return self._match_id

    @property
    def resume_id(self) -> str:
        return self._resume_id

    @property
    def job_id(self) -> str:
        return self._job_id

    @property
    def score(self) -> MatchScore:
        return self._score

    @property
    def gaps(self) -> list[Gap]:
        return list(self._gaps)  # defensive copy

    @property
    def suggestions(self) -> list[ImprovementSuggestion]:
        return list(self._suggestions)

    @property
    def calculated_at(self) -> datetime:
        return self._calculated_at

    @property
    def has_gaps(self) -> bool:
        return len(self._gaps) > 0

    @property
    def high_priority_suggestions(self) -> list[ImprovementSuggestion]:
        return [s for s in self._suggestions if s.priority == "high"]

    def __repr__(self) -> str:
        return (
            f"MatchResult(id={self._match_id!r}, "
            f"resume={self._resume_id!r}, "
            f"job={self._job_id!r}, "
            f"score={self._score.value}, "
            f"gaps={len(self._gaps)})"
        )
