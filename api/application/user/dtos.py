"""
application/user/dtos.py

Commands and read models for the User bounded context.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CreateUserCommand:
    username: str
    email: str
    password: str
    role: str
    first_name: str = ""
    last_name: str = ""


@dataclass(frozen=True)
class UserDTO:
    id: str
    username: str
    email: str
    role: str
