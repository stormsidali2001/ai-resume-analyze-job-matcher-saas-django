"""
domain/user/repositories.py

Abstract repository port for the User bounded context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.user.dtos import CreateUserCommand, UserDTO


class UserRepository(ABC):
    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """Return True if a user with this username already exists."""

    @abstractmethod
    def create(self, cmd: "CreateUserCommand") -> "UserDTO":
        """
        Persist a new user and return its DTO.

        Raises:
            UserAlreadyExistsError: if the username is already taken.
        """
