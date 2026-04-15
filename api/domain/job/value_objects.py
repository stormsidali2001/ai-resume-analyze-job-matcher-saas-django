"""
domain/job/value_objects.py

Value Objects for the Job bounded context.
All are immutable Pydantic v2 BaseModels (frozen=True).
EmploymentType remains a stdlib Enum.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

MIN_JOB_DESCRIPTION_LENGTH: int = 100


class EmploymentType(str, Enum):
    """Allowed employment arrangements for a job posting."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class JobTitle(BaseModel):
    """The title/position name of a job posting."""

    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("JobTitle.value must not be empty.")
        return v

    def __str__(self) -> str:
        return self.value


class CompanyName(BaseModel):
    """The legal or trading name of the hiring company."""

    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("CompanyName.value must not be empty.")
        return v

    def __str__(self) -> str:
        return self.value


class Location(BaseModel):
    """
    Where the job is based. `remote` indicates full remote is allowed.
    """

    model_config = ConfigDict(frozen=True)

    city: str
    country: str
    remote: bool = False

    @field_validator("city", "country")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty.")
        return v

    @property
    def display(self) -> str:
        base = f"{self.city}, {self.country}"
        return f"{base} (Remote)" if self.remote else base


class SalaryRange(BaseModel):
    """
    Salary band offered for the role.
    min_salary must be non-negative; max_salary must be >= min_salary.
    """

    model_config = ConfigDict(frozen=True)

    min_salary: int
    max_salary: int
    currency: str = "USD"

    @field_validator("min_salary")
    @classmethod
    def validate_min(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"SalaryRange.min_salary must be >= 0, got {v}.")
        return v

    @field_validator("currency")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("SalaryRange.currency must not be empty.")
        return v

    @field_validator("max_salary")
    @classmethod
    def validate_max(cls, v: int) -> int:
        # Cross-field check done in model_validator below
        return v

    def model_post_init(self, __context: object) -> None:
        if self.max_salary < self.min_salary:
            raise ValueError(
                f"SalaryRange.max_salary ({self.max_salary}) must be >= "
                f"min_salary ({self.min_salary})."
            )

    @property
    def midpoint(self) -> int:
        return (self.min_salary + self.max_salary) // 2

    @property
    def display(self) -> str:
        return f"{self.currency} {self.min_salary:,} – {self.max_salary:,}"


class JobDescription(BaseModel):
    """
    The full textual description of a job posting.
    Minimum 100 characters.
    """

    model_config = ConfigDict(frozen=True)

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("JobDescription.text must not be empty.")
        if len(v.strip()) < MIN_JOB_DESCRIPTION_LENGTH:
            raise ValueError(
                f"JobDescription.text must be at least "
                f"{MIN_JOB_DESCRIPTION_LENGTH} characters, "
                f"got {len(v.strip())}."
            )
        return v

    @property
    def preview(self) -> str:
        return self.text[:200].strip()
