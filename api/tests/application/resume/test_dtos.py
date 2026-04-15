"""
tests/application/resume/test_dtos.py

Unit tests for resume DTOs and commands — construction and validation.
"""

import pytest
from pydantic import ValidationError

from application.resume.dtos import (
    AddSkillCommand,
    AnalyzeResumeCommand,
    CreateResumeCommand,
    UpdateResumeTextCommand,
)


# ============================================================
# CreateResumeCommand
# ============================================================


class TestCreateResumeCommand:
    def _valid(self, **overrides):
        defaults = dict(
            candidate_id="cand-1",
            raw_text="A" * 100,
            email="alice@example.com",
            phone="+1-555-0100",
            location="New York",
        )
        defaults.update(overrides)
        return CreateResumeCommand(**defaults)

    def test_valid_command(self):
        cmd = self._valid()
        assert cmd.candidate_id == "cand-1"

    @pytest.mark.parametrize("bad_field,value", [
        ("candidate_id", ""),
        ("candidate_id", "   "),
        ("raw_text", ""),
        ("email", ""),
        ("phone", ""),
        ("location", ""),
    ])
    def test_rejects_blank_fields(self, bad_field, value):
        with pytest.raises(ValidationError):
            self._valid(**{bad_field: value})

    @pytest.mark.parametrize("bad_email", ["not-an-email", "nodomain", "missing-at"])
    def test_rejects_invalid_email(self, bad_email):
        with pytest.raises(ValidationError):
            self._valid(email=bad_email)

    def test_accepts_valid_email(self):
        cmd = self._valid(email="user@domain.co.uk")
        assert cmd.email == "user@domain.co.uk"


# ============================================================
# UpdateResumeTextCommand
# ============================================================


class TestUpdateResumeTextCommand:
    def test_valid(self):
        cmd = UpdateResumeTextCommand(
            resume_id="r1",
            candidate_id="c1",
            new_raw_text="Updated content " * 10,
        )
        assert cmd.resume_id == "r1"

    @pytest.mark.parametrize("bad_field,value", [
        ("resume_id", ""),
        ("candidate_id", "   "),
        ("new_raw_text", ""),
    ])
    def test_rejects_blank_fields(self, bad_field, value):
        with pytest.raises(ValidationError):
            UpdateResumeTextCommand(**{
                "resume_id": "r1",
                "candidate_id": "c1",
                "new_raw_text": "ok",
                bad_field: value,
            })


# ============================================================
# AnalyzeResumeCommand
# ============================================================


class TestAnalyzeResumeCommand:
    def test_valid(self):
        cmd = AnalyzeResumeCommand(
            resume_id="r1",
            candidate_id="c1",
            known_skills=["Python", "Django"],
        )
        assert len(cmd.known_skills) == 2

    def test_empty_skills_list_is_valid(self):
        cmd = AnalyzeResumeCommand(resume_id="r1", candidate_id="c1", known_skills=[])
        assert cmd.known_skills == []

    @pytest.mark.parametrize("bad_field,value", [
        ("resume_id", ""),
        ("candidate_id", "   "),
    ])
    def test_rejects_blank_ids(self, bad_field, value):
        with pytest.raises(ValidationError):
            AnalyzeResumeCommand(**{
                "resume_id": "r1",
                "candidate_id": "c1",
                "known_skills": [],
                bad_field: value,
            })


# ============================================================
# AddSkillCommand
# ============================================================


class TestAddSkillCommand:
    def _valid(self, **overrides):
        defaults = dict(
            resume_id="r1",
            candidate_id="c1",
            name="Python",
            category="programming",
            proficiency_level="advanced",
        )
        defaults.update(overrides)
        return AddSkillCommand(**defaults)

    def test_valid(self):
        cmd = self._valid()
        assert cmd.name == "Python"

    @pytest.mark.parametrize("bad_level", ["guru", "pro", "", "EXPERT"])
    def test_rejects_invalid_proficiency(self, bad_level):
        with pytest.raises(ValidationError):
            self._valid(proficiency_level=bad_level)

    @pytest.mark.parametrize("level", ["beginner", "intermediate", "advanced", "expert"])
    def test_accepts_valid_levels(self, level):
        cmd = self._valid(proficiency_level=level)
        assert cmd.proficiency_level == level
