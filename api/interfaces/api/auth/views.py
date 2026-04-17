"""
interfaces/api/auth/views.py

User registration endpoint. Returns JWT tokens upon successful registration.
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from interfaces.api.auth.serializers import RegisterSerializer


class ProfileView(APIView):
    """Return the currently authenticated user's profile."""

    def get(self, request: Request) -> Response:
        user = request.user
        return Response({
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a new user",
        description="Create a candidate or recruiter account. Returns JWT access and refresh tokens immediately.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="User created — returns `user`, `access`, and `refresh` fields"),
            400: OpenApiResponse(description="Validation error (duplicate username, weak password, invalid role)"),
        },
        tags=["Auth"],
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.save()

        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=dto.id)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": {
                    "id": dto.id,
                    "username": dto.username,
                    "email": dto.email,
                    "role": dto.role,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )
