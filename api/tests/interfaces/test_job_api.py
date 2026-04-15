"""
tests/interfaces/test_job_api.py

API tests for job endpoints.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

_DESC = (
    "We need a Senior Python Engineer to architect backend systems, "
    "build scalable REST APIs, and mentor junior developers. " * 3
)


def _create_job_payload(**overrides):
    defaults = dict(
        title="Python Engineer",
        company="TechCorp",
        description=_DESC,
        city="NYC",
        country="USA",
        employment_type="full_time",
        required_experience_months=24,
    )
    defaults.update(overrides)
    return defaults


class TestJobCreate:
    def test_recruiter_can_create_job(self, recruiter_client):
        client, _ = recruiter_client
        resp = client.post("/api/v1/jobs/", _create_job_payload())
        assert resp.status_code == 201
        assert resp.data["status"] == "DRAFT"

    def test_candidate_can_create_job(self, candidate_client):
        """Any authenticated user can create — role enforcement is business logic not HTTP."""
        client, _ = candidate_client
        resp = client.post("/api/v1/jobs/", _create_job_payload())
        assert resp.status_code == 201

    def test_unauthenticated_create_returns_401(self):
        client = APIClient()
        resp = client.post("/api/v1/jobs/", _create_job_payload())
        assert resp.status_code == 401


class TestJobListRetrieve:
    def test_list_is_public(self):
        client = APIClient()
        resp = client.get("/api/v1/jobs/")
        assert resp.status_code == 200

    def test_list_shows_only_published_jobs(self, recruiter_client):
        client, _ = recruiter_client
        # Create draft
        client.post("/api/v1/jobs/", _create_job_payload())
        # Create and publish
        create_resp = client.post("/api/v1/jobs/", _create_job_payload())
        job_id = create_resp.data["job_id"]
        client.post(f"/api/v1/jobs/{job_id}/skills/", {
            "name": "Python", "category": "programming", "proficiency_level": "expert"
        })
        client.post(f"/api/v1/jobs/{job_id}/publish/")

        anon = APIClient()
        resp = anon.get("/api/v1/jobs/")
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["job_id"] == job_id

    def test_retrieve_is_public(self, recruiter_client):
        client, _ = recruiter_client
        create_resp = client.post("/api/v1/jobs/", _create_job_payload())
        job_id = create_resp.data["job_id"]

        anon = APIClient()
        resp = anon.get(f"/api/v1/jobs/{job_id}/")
        assert resp.status_code == 200

    def test_retrieve_nonexistent_returns_404(self):
        anon = APIClient()
        resp = anon.get("/api/v1/jobs/does-not-exist/")
        assert resp.status_code == 404


class TestJobPublishClose:
    def _setup_publishable_job(self, client):
        create_resp = client.post("/api/v1/jobs/", _create_job_payload())
        job_id = create_resp.data["job_id"]
        client.post(f"/api/v1/jobs/{job_id}/skills/", {
            "name": "Python", "category": "programming", "proficiency_level": "expert"
        })
        return job_id

    def test_publish_job(self, recruiter_client):
        client, _ = recruiter_client
        job_id = self._setup_publishable_job(client)
        resp = client.post(f"/api/v1/jobs/{job_id}/publish/")
        assert resp.status_code == 200
        assert resp.data["status"] == "PUBLISHED"

    def test_close_published_job(self, recruiter_client):
        client, _ = recruiter_client
        job_id = self._setup_publishable_job(client)
        client.post(f"/api/v1/jobs/{job_id}/publish/")
        resp = client.post(f"/api/v1/jobs/{job_id}/close/")
        assert resp.status_code == 200
        assert resp.data["status"] == "CLOSED"

    def test_publish_without_skills_returns_422(self, recruiter_client):
        client, _ = recruiter_client
        create_resp = client.post("/api/v1/jobs/", _create_job_payload())
        job_id = create_resp.data["job_id"]
        resp = client.post(f"/api/v1/jobs/{job_id}/publish/")
        assert resp.status_code == 422

    def test_other_recruiter_cannot_publish(self, recruiter_client, candidate_client):
        r_client, _ = recruiter_client
        c_client, _ = candidate_client
        job_id = self._setup_publishable_job(r_client)
        resp = c_client.post(f"/api/v1/jobs/{job_id}/publish/")
        assert resp.status_code == 403
