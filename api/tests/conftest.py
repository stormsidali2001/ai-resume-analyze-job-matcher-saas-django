"""
tests/conftest.py

Shared pytest fixtures for infrastructure and API tests.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def candidate_user(db):
    return User.objects.create_user(
        username="candidate1",
        email="candidate1@example.com",
        password="testpass123",
        role="candidate",
    )


@pytest.fixture
def recruiter_user(db):
    return User.objects.create_user(
        username="recruiter1",
        email="recruiter1@example.com",
        password="testpass123",
        role="recruiter",
    )


@pytest.fixture
def candidate_client(candidate_user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    refresh = RefreshToken.for_user(candidate_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client, candidate_user


@pytest.fixture
def recruiter_client(recruiter_user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    refresh = RefreshToken.for_user(recruiter_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client, recruiter_user
