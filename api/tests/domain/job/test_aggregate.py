"""
tests/domain/job/test_aggregate.py

Unit tests for JobAggregate — creation, mutations, lifecycle, invariants.
"""

import pytest

from domain.common.value_objects import Skill
from domain.job.aggregate import (
    STATUS_CLOSED,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    JobAggregate,
)
from domain.job.exceptions import (
    InvalidJobError,
    JobAlreadyClosedError,
    JobAlreadyPublishedError,
)
from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
    SalaryRange,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def title():
    return JobTitle(value="Senior Python Engineer")


@pytest.fixture
def company():
    return CompanyName(value="TechCorp")


@pytest.fixture
def description():
    return JobDescription(
        text=(
            "We are hiring a Senior Python Engineer to lead backend development. "
            "You will design and build scalable REST APIs using Django and FastAPI. "
            "Strong knowledge of PostgreSQL, Redis, and cloud infrastructure required."
        )
    )


@pytest.fixture
def location():
    return Location(city="San Francisco", country="USA", remote=True)


@pytest.fixture
def skill_python():
    return Skill(name="Python", category="programming", proficiency_level="expert")


@pytest.fixture
def skill_django():
    return Skill(name="Django", category="framework", proficiency_level="advanced")


@pytest.fixture
def draft_job(title, company, description, location, skill_python):
    job = JobAggregate(
        job_id="job-001",
        recruiter_id="rec-001",
        title=title,
        company=company,
        description=description,
        location=location,
        employment_type=EmploymentType.FULL_TIME,
    )
    job.add_required_skill(skill_python)
    return job


# ============================================================
# Construction
# ============================================================


class TestJobAggregateCreation:
    def test_creates_in_draft(self, title, company, description, location):
        job = JobAggregate(
            job_id="j1",
            recruiter_id="r1",
            title=title,
            company=company,
            description=description,
            location=location,
            employment_type=EmploymentType.FULL_TIME,
        )
        assert job.status == STATUS_DRAFT
        assert job.required_skills == []
        assert job.salary_range is None

    def test_creates_with_salary_range(self, title, company, description, location):
        salary = SalaryRange(min_salary=100_000, max_salary=150_000)
        job = JobAggregate(
            job_id="j1",
            recruiter_id="r1",
            title=title,
            company=company,
            description=description,
            location=location,
            employment_type=EmploymentType.CONTRACT,
            salary_range=salary,
        )
        assert job.salary_range == salary

    @pytest.mark.parametrize("bad_id", ["", "   "])
    def test_rejects_empty_job_id(self, bad_id, title, company, description, location):
        with pytest.raises(InvalidJobError):
            JobAggregate(
                job_id=bad_id,
                recruiter_id="r1",
                title=title,
                company=company,
                description=description,
                location=location,
                employment_type=EmploymentType.FULL_TIME,
            )

    @pytest.mark.parametrize("bad_id", ["", "   "])
    def test_rejects_empty_recruiter_id(self, bad_id, title, company, description, location):
        with pytest.raises(InvalidJobError):
            JobAggregate(
                job_id="j1",
                recruiter_id=bad_id,
                title=title,
                company=company,
                description=description,
                location=location,
                employment_type=EmploymentType.FULL_TIME,
            )

    def test_rejects_negative_experience(self, title, company, description, location):
        with pytest.raises(InvalidJobError):
            JobAggregate(
                job_id="j1",
                recruiter_id="r1",
                title=title,
                company=company,
                description=description,
                location=location,
                employment_type=EmploymentType.FULL_TIME,
                required_experience_months=-1,
            )

    def test_rejects_unknown_status(self, title, company, description, location):
        with pytest.raises(InvalidJobError):
            JobAggregate(
                job_id="j1",
                recruiter_id="r1",
                title=title,
                company=company,
                description=description,
                location=location,
                employment_type=EmploymentType.FULL_TIME,
                status="PENDING",
            )


# ============================================================
# add_required_skill
# ============================================================


class TestAddRequiredSkill:
    def test_add_skill(self, draft_job, skill_django):
        draft_job.add_required_skill(skill_django)
        assert skill_django in draft_job.required_skills

    def test_duplicate_skill_is_ignored(self, draft_job, skill_python):
        count_before = len(draft_job.required_skills)
        draft_job.add_required_skill(skill_python)
        assert len(draft_job.required_skills) == count_before

    def test_case_insensitive_dedup(self, draft_job):
        draft_job.add_required_skill(
            Skill(name="python", category="Programming", proficiency_level="intermediate")
        )
        assert len(draft_job.required_skills) == 1

    def test_skills_returns_defensive_copy(self, draft_job, skill_django):
        draft_job.add_required_skill(skill_django)
        copy = draft_job.required_skills
        copy.clear()
        assert len(draft_job.required_skills) == 2

    def test_cannot_add_skill_to_closed_job(self, draft_job, skill_django):
        draft_job.publish()
        draft_job.close()
        with pytest.raises(JobAlreadyClosedError):
            draft_job.add_required_skill(skill_django)


# ============================================================
# update_description
# ============================================================


class TestUpdateDescription:
    def test_update_while_draft(self, draft_job):
        new_desc = JobDescription(
            text="Updated: Looking for a Python architect with Kubernetes experience. "
            "Must have 5+ years of distributed systems design and team leadership."
        )
        draft_job.update_description(new_desc)
        assert draft_job.description == new_desc

    def test_cannot_update_when_published(self, draft_job):
        draft_job.publish()
        with pytest.raises(InvalidJobError, match="DRAFT"):
            draft_job.update_description(JobDescription(text="x" * 100))


# ============================================================
# publish
# ============================================================


class TestPublish:
    def test_publish_valid_draft(self, draft_job):
        draft_job.publish()
        assert draft_job.status == STATUS_PUBLISHED
        assert draft_job.is_published

    def test_publish_raises_if_no_required_skills(self, title, company, description, location):
        job = JobAggregate(
            job_id="j1",
            recruiter_id="r1",
            title=title,
            company=company,
            description=description,
            location=location,
            employment_type=EmploymentType.FULL_TIME,
        )
        with pytest.raises(InvalidJobError, match="skill"):
            job.publish()

    def test_double_publish_raises(self, draft_job):
        draft_job.publish()
        with pytest.raises(JobAlreadyPublishedError):
            draft_job.publish()

    def test_publish_closed_raises(self, draft_job):
        draft_job.publish()
        draft_job.close()
        with pytest.raises(JobAlreadyClosedError):
            draft_job.publish()


# ============================================================
# close
# ============================================================


class TestClose:
    def test_close_published_job(self, draft_job):
        draft_job.publish()
        draft_job.close()
        assert draft_job.status == STATUS_CLOSED
        assert draft_job.is_closed

    def test_close_draft_raises(self, draft_job):
        with pytest.raises(InvalidJobError, match="DRAFT"):
            draft_job.close()

    def test_double_close_raises(self, draft_job):
        draft_job.publish()
        draft_job.close()
        with pytest.raises(JobAlreadyClosedError):
            draft_job.close()


# ============================================================
# validate_for_publishing
# ============================================================


class TestValidateForPublishing:
    def test_valid_job_passes(self, draft_job):
        draft_job.validate_for_publishing()

    def test_no_skills_fails(self, title, company, description, location):
        job = JobAggregate(
            job_id="j1",
            recruiter_id="r1",
            title=title,
            company=company,
            description=description,
            location=location,
            employment_type=EmploymentType.FULL_TIME,
        )
        with pytest.raises(InvalidJobError):
            job.validate_for_publishing()


# ============================================================
# Properties and repr
# ============================================================


class TestProperties:
    def test_is_published_false_when_draft(self, draft_job):
        assert not draft_job.is_published

    def test_is_closed_false_when_published(self, draft_job):
        draft_job.publish()
        assert not draft_job.is_closed

    def test_repr_contains_key_fields(self, draft_job):
        r = repr(draft_job)
        assert "job-001" in r
        assert "DRAFT" in r
