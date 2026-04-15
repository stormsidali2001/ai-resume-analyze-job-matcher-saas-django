"""
application/common/exceptions.py

Application-layer exceptions. These are distinct from domain exceptions:
they wrap domain errors and add context meaningful to callers (API layer).
"""


class ApplicationError(Exception):
    """Base class for all application-layer errors."""


class NotFoundError(ApplicationError):
    """
    Raised when a requested aggregate cannot be found.
    Wraps domain ResumeNotFoundError / JobNotFoundError so the infrastructure
    layer never leaks into callers.
    """

    def __init__(self, resource: str, resource_id: str) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} with id '{resource_id}' was not found.")


class UnauthorizedError(ApplicationError):
    """
    Raised when the requester does not own the resource they are trying
    to access or modify. Not an authentication failure — purely ownership.
    """

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            f"You are not authorised to access {resource} '{resource_id}'."
        )
