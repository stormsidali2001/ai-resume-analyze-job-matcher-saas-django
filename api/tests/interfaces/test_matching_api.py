"""
tests/interfaces/test_matching_api.py

API tests for the matching endpoint.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

_RESUME_TEXT = (
    "Senior Python engineer with 5 years of experience building REST APIs "
    "with Django and FastAPI. Expert in Python and distributed systems. " * 2
)
_JOB_DESC = (
    "We need a Senior Python Engineer to architect backend systems, "
    "build scalable REST APIs using Django, and mentor junior developers. " * 2
)


class TestMatchView:
    def _setup(self, candidate_client, recruiter_client):
        c_client, c_user = candidate_client
        r_client, _ = recruiter_client

        # Create resume
        resume_resp = c_client.post("/api/v1/resumes/", {
            "raw_text": _RESUME_TEXT,
            "email": "c@example.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        resume_id = resume_resp.data["resume_id"]

        # Create job and publish
        job_resp = r_client.post("/api/v1/jobs/", {
            "title": "Python Engineer",
            "company": "TechCorp",
            "description": _JOB_DESC,
            "city": "NYC",
            "country": "USA",
            "employment_type": "full_time",
            "required_experience_months": 24,
        })
        job_id = job_resp.data["job_id"]
        r_client.post(f"/api/v1/jobs/{job_id}/skills/", {
            "name": "Python", "category": "programming", "proficiency_level": "expert"
        })
        r_client.post(f"/api/v1/jobs/{job_id}/publish/")

        return resume_id, job_id

    def test_match_returns_200_with_score(self, candidate_client, recruiter_client):
        c_client, _ = candidate_client
        resume_id, job_id = self._setup(candidate_client, recruiter_client)

        resp = c_client.post("/api/v1/match/", {
            "resume_id": resume_id,
            "job_id": job_id,
        })
        assert resp.status_code == 200
        assert "score" in resp.data
        assert "score_label" in resp.data
        assert 0 <= resp.data["score"] <= 100

    def test_match_requires_auth(self, candidate_client, recruiter_client):
        _, _ = candidate_client
        resume_id, job_id = self._setup(candidate_client, recruiter_client)

        anon = APIClient()
        resp = anon.post("/api/v1/match/", {
            "resume_id": resume_id,
            "job_id": job_id,
        })
        assert resp.status_code == 401

    def test_match_nonexistent_job_returns_404(self, candidate_client):
        c_client, _ = candidate_client
        resume_resp = c_client.post("/api/v1/resumes/", {
            "raw_text": _RESUME_TEXT,
            "email": "c@example.com",
            "phone": "+1-555",
            "location": "NYC",
        })
        resume_id = resume_resp.data["resume_id"]

        resp = c_client.post("/api/v1/match/", {
            "resume_id": resume_id,
            "job_id": "nonexistent-job",
        })
        assert resp.status_code == 404

    def test_match_wrong_owner_returns_403(self, candidate_client, recruiter_client):
        """Recruiter trying to match with a candidate's resume they don't own."""
        c_client, _ = candidate_client
        r_client, _ = recruiter_client
        resume_id, job_id = self._setup(candidate_client, recruiter_client)

        resp = r_client.post("/api/v1/match/", {
            "resume_id": resume_id,
            "job_id": job_id,
        })
        assert resp.status_code == 403
