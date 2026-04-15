"""
interfaces/api/auth/serializers.py

Serializers for user registration.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from application.user.dtos import CreateUserCommand
from interfaces.api.dependencies import get_user_use_cases


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, default="")
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=["candidate", "recruiter"])

    def create(self, validated_data: dict):
        cmd = CreateUserCommand(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            role=validated_data["role"],
        )
        return get_user_use_cases()["create"].execute(cmd)
