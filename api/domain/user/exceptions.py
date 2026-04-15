"""
domain/user/exceptions.py

Domain exceptions for the User bounded context.
"""


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user with a username that is already taken."""
