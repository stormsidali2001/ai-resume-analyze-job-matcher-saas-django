"""
infrastructure/repositories/user.py

Django ORM implementation of UserRepository.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from application.user.dtos import CreateUserCommand, UserDTO
from domain.user.exceptions import UserAlreadyExistsError
from domain.user.repositories import UserRepository

User = get_user_model()


class DjangoUserRepository(UserRepository):
    def exists_by_username(self, username: str) -> bool:
        return User.objects.filter(username=username).exists()

    def create(self, cmd: CreateUserCommand) -> UserDTO:
        try:
            user = User.objects.create_user(
                username=cmd.username,
                email=cmd.email,
                password=cmd.password,
                role=cmd.role,
                first_name=cmd.first_name,
                last_name=cmd.last_name,
            )
        except IntegrityError:
            raise UserAlreadyExistsError(f"Username '{cmd.username}' is already taken.")
        return UserDTO(id=str(user.id), username=user.username, email=user.email, role=user.role)
