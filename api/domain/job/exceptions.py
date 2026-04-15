"""
domain/job/exceptions.py

All domain exceptions for the Job bounded context.
"""


class InvalidJobError(Exception):
    """Raised when a JobAggregate violates a business invariant."""


class JobAlreadyPublishedError(InvalidJobError):
    """Raised when attempting to publish an already-published job."""


class JobAlreadyClosedError(InvalidJobError):
    """Raised when attempting to close or publish an already-closed job."""


class JobNotFoundError(Exception):
    """Raised by JobRepository when no job matches the requested ID."""
