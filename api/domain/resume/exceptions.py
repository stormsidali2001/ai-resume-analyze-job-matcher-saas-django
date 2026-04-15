"""
domain/resume/exceptions.py

All domain exceptions for the Resume bounded context.
"""


class InvalidResumeError(Exception):
    """Raised when a ResumeAggregate violates a business invariant."""


class DuplicateSkillError(InvalidResumeError):
    """Raised when adding a skill that already exists (same name + category)."""


class ResumeNotFoundError(Exception):
    """Raised by ResumeRepository when no resume matches the requested ID."""
