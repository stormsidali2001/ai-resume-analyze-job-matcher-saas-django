"""
domain/resume/aggregate.py

ResumeAggregate — the consistency boundary for everything related to a
single candidate's resume. All mutations go through this class so that
business invariants are always enforced.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from domain.common.value_objects import Skill
from domain.resume.exceptions import DuplicateSkillError, InvalidResumeError
from domain.resume.value_objects import (
    ContactInfo,
    Education,
    Experience,
    RawResumeContent,
)

# Allowed lifecycle states
STATUS_DRAFT: Final[str] = "DRAFT"
STATUS_ACTIVE: Final[str] = "ACTIVE"
STATUS_ARCHIVED: Final[str] = "ARCHIVED"
VALID_STATUSES: Final[frozenset[str]] = frozenset(
    {STATUS_DRAFT, STATUS_ACTIVE, STATUS_ARCHIVED}
)


class ResumeAggregate:
    """
    Aggregate root for a candidate's resume.

    Identity: resume_id (str)
    Invariants:
        - resume_id and candidate_id must be non-empty strings
        - Skill names+categories must be unique within the resume
        - An ARCHIVED resume cannot be modified
    """

    def __init__(
        self,
        resume_id: str,
        candidate_id: str,
        raw_text: RawResumeContent,
        contact_info: ContactInfo,
        skills: list[Skill] | None = None,
        experiences: list[Experience] | None = None,
        education: list[Education] | None = None,
        status: str = STATUS_DRAFT,
        analysis_status: str = "idle",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        if not resume_id or not resume_id.strip():
            raise InvalidResumeError("ResumeAggregate.resume_id must not be empty.")
        if not candidate_id or not candidate_id.strip():
            raise InvalidResumeError("ResumeAggregate.candidate_id must not be empty.")
        if status not in VALID_STATUSES:
            raise InvalidResumeError(
                f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}."
            )

        self._resume_id = resume_id
        self._candidate_id = candidate_id
        self._raw_text = raw_text
        self._contact_info = contact_info
        self._skills: list[Skill] = list(skills or [])
        self._experiences: list[Experience] = list(experiences or [])
        self._education: list[Education] = list(education or [])
        self._status = status
        self._analysis_status = analysis_status
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)

        # Validate initial skill list for duplicates
        self._assert_no_duplicate_skills(self._skills)

    # ------------------------------------------------------------------
    # Identity & read-only properties
    # ------------------------------------------------------------------

    @property
    def resume_id(self) -> str:
        return self._resume_id

    @property
    def candidate_id(self) -> str:
        return self._candidate_id

    @property
    def raw_text(self) -> RawResumeContent:
        return self._raw_text

    @property
    def contact_info(self) -> ContactInfo:
        return self._contact_info

    @property
    def skills(self) -> list[Skill]:
        return list(self._skills)  # defensive copy

    @property
    def experiences(self) -> list[Experience]:
        return list(self._experiences)

    @property
    def education(self) -> list[Education]:
        return list(self._education)

    @property
    def status(self) -> str:
        return self._status

    @property
    def analysis_status(self) -> str:
        return self._analysis_status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def total_experience_months(self) -> int:
        return sum(e.duration_months for e in self._experiences)

    # ------------------------------------------------------------------
    # Mutation methods (enforce invariants)
    # ------------------------------------------------------------------

    def add_skill(self, skill: Skill) -> None:
        """Add a skill. Raises DuplicateSkillError if same name+category exists."""
        self._assert_not_archived()
        for existing in self._skills:
            if existing.matches(skill):
                raise DuplicateSkillError(
                    f"Skill '{skill.name}' in category '{skill.category}' "
                    f"already exists on this resume."
                )
        self._skills.append(skill)
        self._touch()

    def add_experience(self, experience: Experience) -> None:
        """Append a work experience entry."""
        self._assert_not_archived()
        self._experiences.append(experience)
        self._touch()

    def add_education(self, education: Education) -> None:
        """Append an education entry."""
        self._assert_not_archived()
        self._education.append(education)
        self._touch()

    def update_contact_info(self, contact_info: ContactInfo) -> None:
        """Replace contact information."""
        self._assert_not_archived()
        self._contact_info = contact_info
        self._touch()

    def update_raw_text(self, content: RawResumeContent) -> None:
        """Replace the raw resume text (e.g. after re-upload)."""
        self._assert_not_archived()
        self._raw_text = content
        self._touch()

    def update_from_parsed_text(
        self,
        skills: list[Skill],
        experiences: list[Experience],
        education: list[Education],
    ) -> None:
        """
        Bulk-replace skills, experiences, and education after an AI parse.
        Validates the new skill list for internal duplicates before committing.
        """
        self._assert_not_archived()
        self._assert_no_duplicate_skills(skills)
        self._skills = list(skills)
        self._experiences = list(experiences)
        self._education = list(education)
        self._touch()

    def activate(self) -> None:
        """Transition from DRAFT → ACTIVE after consistency check."""
        self._assert_not_archived()
        self.validate_consistency()
        self._status = STATUS_ACTIVE
        self._touch()

    def archive(self) -> None:
        """Mark the resume as ARCHIVED. No further modifications allowed."""
        if self._status == STATUS_ARCHIVED:
            raise InvalidResumeError("Resume is already archived.")
        self._status = STATUS_ARCHIVED
        self._touch()

    def validate_consistency(self) -> None:
        """
        Ensure the resume is internally consistent enough to be useful.
        Raises InvalidResumeError listing all violations found.
        """
        errors: list[str] = []
        if not self._skills and not self._experiences:
            errors.append(
                "Resume must have at least one skill or one work experience."
            )
        if errors:
            raise InvalidResumeError(
                "Resume failed consistency check: " + "; ".join(errors)
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _touch(self) -> None:
        self._updated_at = datetime.now(timezone.utc)

    def _assert_not_archived(self) -> None:
        if self._status == STATUS_ARCHIVED:
            raise InvalidResumeError(
                "Cannot modify an archived resume."
            )

    @staticmethod
    def _assert_no_duplicate_skills(skills: list[Skill]) -> None:
        seen: set[tuple[str, str]] = set()
        for skill in skills:
            key = (skill.normalised_name, skill.normalised_category)
            if key in seen:
                raise DuplicateSkillError(
                    f"Duplicate skill detected: '{skill.name}' "
                    f"in category '{skill.category}'."
                )
            seen.add(key)

    def __repr__(self) -> str:
        return (
            f"ResumeAggregate(id={self._resume_id!r}, "
            f"candidate={self._candidate_id!r}, "
            f"status={self._status!r}, "
            f"skills={len(self._skills)}, "
            f"experiences={len(self._experiences)})"
        )
