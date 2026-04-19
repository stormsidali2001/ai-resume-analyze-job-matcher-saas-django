"""
application/resume/dtos.py

Pydantic v2 Data Transfer Objects and Commands for the Resume context.
DTOs are read models (output); Commands are write models (input).
None of these contain business logic — they are pure data carriers.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from domain.common.value_objects import VALID_PROFICIENCY_LEVELS


# ---------------------------------------------------------------------------
# Sub-DTOs (nested read models)
# ---------------------------------------------------------------------------


class SkillDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    category: str
    proficiency_level: str


class ExperienceDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: str
    company: str
    duration_months: int
    responsibilities: list[str]


class EducationDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    degree: str
    institution: str
    graduation_year: int


class ContactInfoDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str
    phone: str
    location: str


# ---------------------------------------------------------------------------
# Resume read model
# ---------------------------------------------------------------------------


class ResumeDTO(BaseModel):
    """Full resume read model returned by use cases."""

    model_config = ConfigDict(frozen=True)

    resume_id: str
    candidate_id: str
    status: str
    analysis_status: str
    raw_text_preview: str
    contact_info: ContactInfoDTO
    skills: list[SkillDTO]
    experiences: list[ExperienceDTO]
    education: list[EducationDTO]
    total_experience_months: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# AI parsing result
# ---------------------------------------------------------------------------


class ParsedResumeData(BaseModel):
    """Output model returned by AIAnalysisPort implementations."""

    model_config = ConfigDict(frozen=True)

    skills: list[SkillDTO]
    experiences: list[ExperienceDTO]
    education: list[EducationDTO]


# ---------------------------------------------------------------------------
# Commands (input models)
# ---------------------------------------------------------------------------


class CreateResumeCommand(BaseModel):
    """Command to create a new resume for a candidate."""

    candidate_id: str
    raw_text: str
    email: str
    phone: str
    location: str

    @field_validator("candidate_id", "raw_text", "email", "phone", "location")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v

    @field_validator("email")
    @classmethod
    def email_must_have_at(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("email must contain '@'.")
        return v


class UpdateResumeTextCommand(BaseModel):
    """Command to replace the raw text on an existing resume."""

    resume_id: str
    candidate_id: str
    new_raw_text: str

    @field_validator("resume_id", "candidate_id", "new_raw_text")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v


class AnalyzeResumeCommand(BaseModel):
    """Command to trigger rule-based skill extraction on a resume."""

    resume_id: str
    candidate_id: str
    known_skills: list[str]

    @field_validator("resume_id", "candidate_id")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v


class AddSkillCommand(BaseModel):
    """Command to manually add a skill to a resume."""

    resume_id: str
    candidate_id: str
    name: str
    category: str
    proficiency_level: str

    @field_validator("resume_id", "candidate_id", "name", "category")
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
