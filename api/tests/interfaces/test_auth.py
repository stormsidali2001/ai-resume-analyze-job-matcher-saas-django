"""
tests/interfaces/test_auth.py

API tests for authentication endpoints.
"""

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestRegisterView:
    def test_register_candidate_returns_201(self):
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "newcandidate",
            "email": "new@example.com",
            "password": "Str0ngPass!99",
            "role": "candidate",
        })
        assert resp.status_code == 201
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["role"] == "candidate"

    def test_register_recruiter_returns_201(self):
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "newrecruiter",
            "email": "recruiter@example.com",
            "password": "Str0ngPass!99",
            "role": "recruiter",
        })
        assert resp.status_code == 201
        assert resp.data["user"]["role"] == "recruiter"

    def test_duplicate_username_returns_409(self, candidate_user):
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": candidate_user.username,
            "email": "other@example.com",
            "password": "Str0ngPass!99",
            "role": "candidate",
        })
        assert resp.status_code == 409

    def test_invalid_role_returns_400(self):
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Str0ngPass!99",
            "role": "admin",
        })
        assert resp.status_code == 400


class TestTokenEndpoints:
    def test_obtain_token(self, candidate_user):
        client = APIClient()
        resp = client.post("/api/auth/token/", {
            "username": candidate_user.username,
            "password": "testpass123",
        })
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_refresh_token(self, candidate_user):
        client = APIClient()
        resp = client.post("/api/auth/token/", {
            "username": candidate_user.username,
            "password": "testpass123",
        })
        refresh = resp.data["refresh"]

        resp2 = client.post("/api/auth/token/refresh/", {"refresh": refresh})
        assert resp2.status_code == 200
        assert "access" in resp2.data
