"""
application/user/use_cases.py

Application use cases for the User bounded context.
"""

from __future__ import annotations

from application.user.dtos import CreateUserCommand, UserDTO
from domain.user.exceptions import UserAlreadyExistsError
from domain.user.repositories import UserRepository


class CreateUserUseCase:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def execute(self, cmd: CreateUserCommand) -> UserDTO:
        if self._repo.exists_by_username(cmd.username):
            raise UserAlreadyExistsError(f"Username '{cmd.username}' is already taken.")
        return self._repo.create(cmd)
