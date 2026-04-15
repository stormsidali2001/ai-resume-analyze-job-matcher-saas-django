"""
tests/interfaces/test_resume_api.py

API tests for resume endpoints — full lifecycle.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db

_LONG_TEXT = (
    "Senior Python engineer with 7 years of experience building distributed "
    "systems, REST APIs, and cloud-native applications using Django and FastAPI. " * 2
)


class TestResumeCreate:
    def test_create_resume_returns_201(self, candidate_client):
        client, user = candidate_client
        resp = client.post("/api/v1/resumes/", {
            "raw_text": _LONG_TEXT,
            "email": "me@example.com",
            "phone": "+1-555-0100",
            "location": "NYC",
        })
        assert resp.status_code == 201
        assert resp.data["candidate_id"] == str(user.id)
        assert resp.data["status"] == "DRAFT"

    def test_create_requires_auth(self):
        from rest_framework.test import APIClient
        client = APIClient()
        resp = client.post("/api/v1/resumes/", {"raw_text": _LONG_TEXT})
        assert resp.status_code == 401

    def test_create_with_short_text_returns_422(self, candidate_client):
        client, _ = candidate_client
        resp = client.post("/api/v1/resumes/", {
            "raw_text": "too short",
            "email": "me@example.com",
            "phone": "+1-000",
            "location": "NYC",
        })
        assert resp.status_code in (400, 422)


class TestResumeList:
    def test_list_returns_own_resumes(self, candidate_client):
        client, user = candidate_client
        client.post("/api/v1/resumes/", {
            "raw_text": _LONG_TEXT,
            "email": "me@example.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        resp = client.get("/api/v1/resumes/")
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_list_does_not_include_others_resumes(self, candidate_client, recruiter_client):
        """Two users — each sees only their own resumes."""
        c1, _ = candidate_client
        c1.post("/api/v1/resumes/", {
            "raw_text": _LONG_TEXT,
            "email": "a@b.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        c2, _ = recruiter_client
        resp = c2.get("/api/v1/resumes/")
        assert resp.status_code == 200
        assert len(resp.data) == 0


class TestResumeRetrieve:
    def test_owner_can_retrieve(self, candidate_client):
        client, _ = candidate_client
        create_resp = client.post("/api/v1/resumes/", {
            "raw_text": _LONG_TEXT,
            "email": "me@example.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        resume_id = create_resp.data["resume_id"]
        resp = client.get(f"/api/v1/resumes/{resume_id}/")
        assert resp.status_code == 200
        assert resp.data["resume_id"] == resume_id

    def test_other_user_gets_403(self, candidate_client, recruiter_client):
        c1, _ = candidate_client
        c2, _ = recruiter_client
        create_resp = c1.post("/api/v1/resumes/", {
            "raw_text": _LONG_TEXT,
            "email": "me@example.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        resume_id = create_resp.data["resume_id"]
        resp = c2.get(f"/api/v1/resumes/{resume_id}/")
        assert resp.status_code == 403

    def test_nonexistent_resume_returns_404(self, candidate_client):
        client, _ = candidate_client
        resp = client.get("/api/v1/resumes/nonexistent-id/")
        assert resp.status_code == 404


class TestResumeAddSkill:
    def test_add_skill_returns_201(self, candidate_client):
        client, _ = candidate_client
        create_resp = client.post("/api/v1/resumes/", {
            "raw_text": _LONG_TEXT,
            "email": "me@example.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        resume_id = create_resp.data["resume_id"]

        resp = client.post(f"/api/v1/resumes/{resume_id}/skills/", {
            "name": "Python",
            "category": "programming",
            "proficiency_level": "expert",
        })
        assert resp.status_code == 201
        skill_names = [s["name"] for s in resp.data["skills"]]
        assert "Python" in skill_names


class TestResumeArchive:
    def test_archive_returns_204(self, candidate_client):
        client, _ = candidate_client
        create_resp = client.post("/api/v1/resumes/", {
            "raw_text": _LONG_TEXT,
            "email": "me@example.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        resume_id = create_resp.data["resume_id"]

        resp = client.post(f"/api/v1/resumes/{resume_id}/archive/")
        assert resp.status_code == 204
