"""
application/job/dtos.py

Pydantic v2 DTOs and Commands for the Job context.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from application.resume.dtos import SkillDTO
from domain.common.value_objects import VALID_PROFICIENCY_LEVELS


# ---------------------------------------------------------------------------
# Sub-DTOs
# ---------------------------------------------------------------------------


class LocationDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    city: str
    country: str
    remote: bool = False


class SalaryRangeDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    min_salary: int
    max_salary: int
    currency: str = "USD"


# ---------------------------------------------------------------------------
# Job read model
# ---------------------------------------------------------------------------


class JobDTO(BaseModel):
    """Full job read model returned by use cases."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    recruiter_id: str
    title: str
    company: str
    description_preview: str
    required_skills: list[SkillDTO]
    required_experience_months: int
    location: LocationDTO
    employment_type: str
    salary_range: Optional[SalaryRangeDTO]
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


class CreateJobCommand(BaseModel):
    """Command to create a new job posting."""

    recruiter_id: str
    title: str
    company: str
    description: str
    city: str
    country: str
    remote: bool = False
    employment_type: str
    required_experience_months: int = 0
    salary_range: Optional[SalaryRangeDTO] = None

    @field_validator("recruiter_id", "title", "company", "description", "city", "country")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v

    @field_validator("required_experience_months")
    @classmethod
    def must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("required_experience_months must be >= 0.")
        return v


class AddSkillToJobCommand(BaseModel):
    """Command to add a required skill to a job posting."""

    job_id: str
    recruiter_id: str
    name: str
    category: str
    proficiency_level: str

    @field_validator("job_id", "recruiter_id", "name", "category")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v

    @field_validator("proficiency_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if v not in VALID_PROFICIENCY_LEVELS:
            raise ValueError(
                f"proficiency_level must be one of {sorted(VALID_PROFICIENCY_LEVELS)}."
            )
        return v


class UpdateJobDescriptionCommand(BaseModel):
    """Command to update the description of a DRAFT job."""

    job_id: str
    recruiter_id: str
    new_description: str

    @field_validator("job_id", "recruiter_id", "new_description")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v
