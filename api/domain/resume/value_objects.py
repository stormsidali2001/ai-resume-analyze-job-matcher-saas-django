"""
domain/resume/value_objects.py

Value Objects specific to the Resume bounded context.
All are immutable Pydantic v2 BaseModels (frozen=True).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

MIN_RESUME_TEXT_LENGTH: int = 50
MIN_GRADUATION_YEAR: int = 1900
MAX_GRADUATION_YEAR: int = 2100


class RawResumeContent(BaseModel):
    """
    The raw extracted text from a resume document (PDF/DOCX).
    Must contain meaningful content — at least 50 characters.
    """

    model_config = ConfigDict(frozen=True)

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("RawResumeContent.text must not be empty.")
        if len(v.strip()) < MIN_RESUME_TEXT_LENGTH:
            raise ValueError(
                f"RawResumeContent.text must be at least {MIN_RESUME_TEXT_LENGTH} "
                f"characters, got {len(v.strip())}."
            )
        return v

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def preview(self) -> str:
        return self.text[:120].strip()


class ContactInfo(BaseModel):
    """
    A candidate's contact details. Email is required and format-validated.
    """

    model_config = ConfigDict(frozen=True)

    email: str
    phone: str
    location: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ContactInfo.email must not be empty.")
        if "@" not in v:
            raise ValueError(
                f"ContactInfo.email must contain '@', got {v!r}."
            )
        return v

    @field_validator("phone", "location")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty.")
        return v


class Experience(BaseModel):
    """
    A single work-experience entry on a resume.

    `responsibilities` is stored as a tuple (immutable). Pydantic v2
    automatically coerces list[str] → tuple[str, ...].
    """

    model_config = ConfigDict(frozen=True)

    role: str
    company: str
    duration_months: int
    responsibilities: tuple[str, ...] = ()

    @field_validator("role", "company")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty.")
        return v

    @field_validator("duration_months")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v < 0:
            raise ValueError(
                f"Experience.duration_months must be >= 0, got {v}."
            )
        return v

    @property
    def duration_years(self) -> float:
        return round(self.duration_months / 12, 1)


class Education(BaseModel):
    """
    A single educational qualification on a resume.
    graduation_year must be a plausible calendar year.
    """

    model_config = ConfigDict(frozen=True)

    degree: str
    institution: str
    graduation_year: int

    @field_validator("degree", "institution")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty.")
        return v

    @field_validator("graduation_year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if not (MIN_GRADUATION_YEAR <= v <= MAX_GRADUATION_YEAR):
            raise ValueError(
                f"Education.graduation_year must be between "
                f"{MIN_GRADUATION_YEAR} and {MAX_GRADUATION_YEAR}, got {v}."
            )
        return v
