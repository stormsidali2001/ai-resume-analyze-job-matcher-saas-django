"""
interfaces/api/exceptions.py

Custom DRF exception handler that maps domain and application exceptions
to appropriate HTTP responses.
"""

from __future__ import annotations

from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from application.common.exceptions import NotFoundError, UnauthorizedError
from domain.job.exceptions import (
    InvalidJobError,
    JobAlreadyClosedError,
    JobAlreadyPublishedError,
)
from domain.resume.exceptions import DuplicateSkillError, InvalidResumeError
from domain.user.exceptions import UserAlreadyExistsError


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    # Let DRF handle its own exceptions first (returns Response or None)
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, NotFoundError):
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, UnauthorizedError):
        return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, (InvalidResumeError, InvalidJobError)):
        return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if isinstance(exc, DuplicateSkillError):
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, (JobAlreadyPublishedError, JobAlreadyClosedError)):
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, UserAlreadyExistsError):
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, PydanticValidationError):
        # Pydantic v2 ctx dicts can hold raw exception objects — make everything str-safe
        def _safe(obj):
            if isinstance(obj, dict):
                return {k: _safe(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_safe(i) for i in obj]
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            return str(obj)

        errors = [_safe(err) for err in exc.errors(include_url=False)]
        return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"detail": "An unexpected error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
