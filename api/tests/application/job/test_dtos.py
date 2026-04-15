"""
tests/application/job/test_dtos.py

Unit tests for job DTOs and commands.
"""

import pytest
from pydantic import ValidationError

from application.job.dtos import (
    AddSkillToJobCommand,
    CreateJobCommand,
    SalaryRangeDTO,
    UpdateJobDescriptionCommand,
)

_LONG_DESC = "We are looking for a Senior Python Engineer to lead backend development. " * 3


# ============================================================
# CreateJobCommand
# ============================================================


class TestCreateJobCommand:
    def _valid(self, **overrides):
        defaults = dict(
            recruiter_id="rec-1",
            title="Python Engineer",
            company="TechCorp",
            description=_LONG_DESC,
            city="NYC",
            country="USA",
            employment_type="full_time",
            required_experience_months=24,
        )
        defaults.update(overrides)
        return CreateJobCommand(**defaults)

    def test_valid_command(self):
        cmd = self._valid()
        assert cmd.recruiter_id == "rec-1"
        assert cmd.remote is False

    def test_remote_flag_defaults_false(self):
        assert self._valid().remote is False

    def test_accepts_salary_range(self):
        cmd = self._valid(salary_range=SalaryRangeDTO(min_salary=80_000, max_salary=120_000))
        assert cmd.salary_range is not None

    def test_salary_range_optional(self):
        assert self._valid().salary_range is None

    @pytest.mark.parametrize("bad_field,value", [
        ("recruiter_id", ""),
        ("title", "   "),
        ("company", ""),
        ("description", ""),
        ("city", ""),
        ("country", "   "),
    ])
    def test_rejects_blank_fields(self, bad_field, value):
        with pytest.raises(ValidationError):
            self._valid(**{bad_field: value})

    def test_rejects_negative_experience(self):
        with pytest.raises(ValidationError):
            self._valid(required_experience_months=-1)

    def test_zero_experience_is_valid(self):
        cmd = self._valid(required_experience_months=0)
        assert cmd.required_experience_months == 0


# ============================================================
# AddSkillToJobCommand
# ============================================================


class TestAddSkillToJobCommand:
    def _valid(self, **overrides):
        defaults = dict(
            job_id="j1",
            recruiter_id="r1",
            name="Python",
            category="programming",
            proficiency_level="advanced",
        )
        defaults.update(overrides)
        return AddSkillToJobCommand(**defaults)

    def test_valid(self):
        cmd = self._valid()
        assert cmd.name == "Python"

    @pytest.mark.parametrize("bad_level", ["guru", "", "EXPERT"])
    def test_rejects_invalid_proficiency(self, bad_level):
        with pytest.raises(ValidationError):
            self._valid(proficiency_level=bad_level)

    @pytest.mark.parametrize("field", ["job_id", "recruiter_id", "name", "category"])
    def test_rejects_blank_required_fields(self, field):
        with pytest.raises(ValidationError):
            self._valid(**{field: ""})


# ============================================================
# UpdateJobDescriptionCommand
# ============================================================


class TestUpdateJobDescriptionCommand:
    def test_valid(self):
        cmd = UpdateJobDescriptionCommand(
            job_id="j1", recruiter_id="r1", new_description="x" * 50
        )
        assert cmd.job_id == "j1"

    @pytest.mark.parametrize("field", ["job_id", "recruiter_id", "new_description"])
    def test_rejects_blank_fields(self, field):
        with pytest.raises(ValidationError):
            UpdateJobDescriptionCommand(**{
                "job_id": "j1",
                "recruiter_id": "r1",
                "new_description": "ok",
                field: "",
            })
