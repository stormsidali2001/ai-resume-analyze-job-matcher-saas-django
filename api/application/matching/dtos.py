"""
application/matching/dtos.py

Pydantic v2 DTOs and Commands for the Matching context.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class GapDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    gap_type: str
    description: str


class SuggestionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    priority: str
    category: str


class MatchResultDTO(BaseModel):
    """Full match result read model."""

    model_config = ConfigDict(frozen=True)

    match_id: str
    resume_id: str
    job_id: str
    score: int
    score_label: str
    gaps: list[GapDTO]
    suggestions: list[SuggestionDTO]
    calculated_at: datetime


class MatchRequestCommand(BaseModel):
    """Command to trigger a resume–job match calculation."""

    resume_id: str
    candidate_id: str
    job_id: str

    @field_validator("resume_id", "candidate_id", "job_id")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v


class BatchMatchCommand(BaseModel):
    """Command to score one resume against multiple jobs concurrently."""

    resume_id: str
    candidate_id: str
    job_ids: list[str]

    @field_validator("resume_id", "candidate_id")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v

    @field_validator("job_ids")
    @classmethod
    def validate_job_ids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("job_ids must contain at least one job ID.")
        if len(v) > 10:
            raise ValueError("job_ids may contain at most 10 job IDs.")
        return v
