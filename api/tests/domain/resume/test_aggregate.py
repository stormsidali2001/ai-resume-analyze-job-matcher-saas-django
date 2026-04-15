"""
tests/domain/resume/test_aggregate.py

Unit tests for ResumeAggregate — creation, mutations, invariants, lifecycle.
"""

import pytest

from domain.common.value_objects import Skill
from domain.resume.aggregate import (
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    STATUS_DRAFT,
    ResumeAggregate,
)
from domain.resume.exceptions import DuplicateSkillError, InvalidResumeError
from domain.resume.value_objects import (
    ContactInfo,
    Education,
    Experience,
    RawResumeContent,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def raw_text():
    return RawResumeContent(
        text="Senior Python engineer with 7 years building distributed systems "
        "and REST APIs. Expert in Django, FastAPI, and PostgreSQL."
    )


@pytest.fixture
def contact():
    return ContactInfo(email="alice@example.com", phone="+1-555-0100", location="NYC")


@pytest.fixture
def skill_python():
    return Skill(name="Python", category="programming", proficiency_level="expert")


@pytest.fixture
def skill_django():
    return Skill(name="Django", category="framework", proficiency_level="advanced")


@pytest.fixture
def experience():
    return Experience(
        role="Senior Engineer",
        company="Acme Corp",
        duration_months=36,
        responsibilities=["Led a team of 5", "Shipped REST APIs"],
    )


@pytest.fixture
def education():
    return Education(degree="B.Sc. CS", institution="MIT", graduation_year=2017)


@pytest.fixture
def resume(raw_text, contact):
    return ResumeAggregate(
        resume_id="resume-001",
        candidate_id="cand-001",
        raw_text=raw_text,
        contact_info=contact,
    )


# ============================================================
# Construction
# ============================================================


class TestResumeAggregateCreation:
    def test_creates_with_required_fields(self, raw_text, contact):
        r = ResumeAggregate(
            resume_id="r1",
            candidate_id="c1",
            raw_text=raw_text,
            contact_info=contact,
        )
        assert r.resume_id == "r1"
        assert r.candidate_id == "c1"
        assert r.status == STATUS_DRAFT
        assert r.skills == []
        assert r.experiences == []
        assert r.education == []

    def test_creates_with_initial_skills(self, raw_text, contact, skill_python):
        r = ResumeAggregate(
            resume_id="r1",
            candidate_id="c1",
            raw_text=raw_text,
            contact_info=contact,
            skills=[skill_python],
        )
        assert len(r.skills) == 1

    @pytest.mark.parametrize("bad_id", ["", "   "])
    def test_rejects_empty_resume_id(self, bad_id, raw_text, contact):
        with pytest.raises(InvalidResumeError):
            ResumeAggregate(
                resume_id=bad_id,
                candidate_id="c1",
                raw_text=raw_text,
                contact_info=contact,
            )

    @pytest.mark.parametrize("bad_id", ["", "   "])
    def test_rejects_empty_candidate_id(self, bad_id, raw_text, contact):
        with pytest.raises(InvalidResumeError):
            ResumeAggregate(
                resume_id="r1",
                candidate_id=bad_id,
                raw_text=raw_text,
                contact_info=contact,
            )

    def test_rejects_invalid_status(self, raw_text, contact):
        with pytest.raises(InvalidResumeError):
            ResumeAggregate(
                resume_id="r1",
                candidate_id="c1",
                raw_text=raw_text,
                contact_info=contact,
                status="UNKNOWN",
            )

    def test_rejects_duplicate_skills_at_construction(self, raw_text, contact, skill_python):
        with pytest.raises(DuplicateSkillError):
            ResumeAggregate(
                resume_id="r1",
                candidate_id="c1",
                raw_text=raw_text,
                contact_info=contact,
                skills=[skill_python, skill_python],
            )

    def test_total_experience_months_empty(self, resume):
        assert resume.total_experience_months == 0


# ============================================================
# add_skill
# ============================================================


class TestAddSkill:
    def test_add_skill_succeeds(self, resume, skill_python):
        resume.add_skill(skill_python)
        assert skill_python in resume.skills

    def test_add_multiple_distinct_skills(self, resume, skill_python, skill_django):
        resume.add_skill(skill_python)
        resume.add_skill(skill_django)
        assert len(resume.skills) == 2

    def test_duplicate_skill_raises(self, resume, skill_python):
        resume.add_skill(skill_python)
        with pytest.raises(DuplicateSkillError):
            resume.add_skill(skill_python)

    def test_case_insensitive_duplicate_detection(self, resume):
        resume.add_skill(Skill(name="Python", category="programming", proficiency_level="expert"))
        with pytest.raises(DuplicateSkillError):
            resume.add_skill(Skill(name="python", category="Programming", proficiency_level="beginner"))

    def test_skills_returns_defensive_copy(self, resume, skill_python):
        resume.add_skill(skill_python)
        copy = resume.skills
        copy.append(Skill(name="SQL", category="database", proficiency_level="intermediate"))
        assert len(resume.skills) == 1

    def test_add_skill_updates_updated_at(self, resume, skill_python):
        before = resume.updated_at
        resume.add_skill(skill_python)
        assert resume.updated_at >= before


# ============================================================
# add_experience / add_education / update_contact_info
# ============================================================


class TestAddExperienceAndEducation:
    def test_add_experience(self, resume, experience):
        resume.add_experience(experience)
        assert experience in resume.experiences

    def test_total_experience_months_accumulates(self, resume):
        resume.add_experience(Experience(role="Dev", company="A", duration_months=12, responsibilities=[]))
        resume.add_experience(Experience(role="Lead", company="B", duration_months=24, responsibilities=[]))
        assert resume.total_experience_months == 36

    def test_add_education(self, resume, education):
        resume.add_education(education)
        assert education in resume.education

    def test_update_contact_info(self, resume):
        new_contact = ContactInfo(
            email="new@example.com", phone="+44-20-1234", location="London"
        )
        resume.update_contact_info(new_contact)
        assert resume.contact_info == new_contact

    def test_update_raw_text(self, resume):
        new_text = RawResumeContent(text="Updated resume content. " * 5)
        resume.update_raw_text(new_text)
        assert resume.raw_text == new_text


# ============================================================
# update_from_parsed_text
# ============================================================


class TestUpdateFromParsedText:
    def test_bulk_replace(self, resume, skill_python, experience, education):
        resume.update_from_parsed_text(
            skills=[skill_python],
            experiences=[experience],
            education=[education],
        )
        assert len(resume.skills) == 1
        assert len(resume.experiences) == 1
        assert len(resume.education) == 1

    def test_clears_existing_data(self, resume, skill_python, skill_django):
        resume.add_skill(skill_python)
        resume.update_from_parsed_text(
            skills=[skill_django],
            experiences=[],
            education=[],
        )
        assert resume.skills == [skill_django]

    def test_rejects_duplicate_skills_in_bulk(self, resume, skill_python):
        with pytest.raises(DuplicateSkillError):
            resume.update_from_parsed_text(
                skills=[skill_python, skill_python],
                experiences=[],
                education=[],
            )


# ============================================================
# validate_consistency
# ============================================================


class TestValidateConsistency:
    def test_passes_with_skills(self, resume, skill_python):
        resume.add_skill(skill_python)
        resume.validate_consistency()

    def test_passes_with_experience(self, resume, experience):
        resume.add_experience(experience)
        resume.validate_consistency()

    def test_fails_when_empty(self, resume):
        with pytest.raises(InvalidResumeError, match="consistency"):
            resume.validate_consistency()


# ============================================================
# Lifecycle: activate / archive
# ============================================================


class TestLifecycle:
    def test_activate_transitions_to_active(self, resume, skill_python):
        resume.add_skill(skill_python)
        resume.activate()
        assert resume.status == STATUS_ACTIVE

    def test_activate_fails_without_content(self, resume):
        with pytest.raises(InvalidResumeError):
            resume.activate()

    def test_archive_from_draft(self, resume):
        resume.archive()
        assert resume.status == STATUS_ARCHIVED

    def test_archive_from_active(self, resume, skill_python):
        resume.add_skill(skill_python)
        resume.activate()
        resume.archive()
        assert resume.status == STATUS_ARCHIVED

    def test_double_archive_raises(self, resume):
        resume.archive()
        with pytest.raises(InvalidResumeError):
            resume.archive()

    def test_add_skill_raises_on_archived(self, resume, skill_python):
        resume.archive()
        with pytest.raises(InvalidResumeError, match="archived"):
            resume.add_skill(skill_python)

    def test_add_experience_raises_on_archived(self, resume, experience):
        resume.archive()
        with pytest.raises(InvalidResumeError, match="archived"):
            resume.add_experience(experience)

    def test_update_contact_raises_on_archived(self, resume, contact):
        resume.archive()
        with pytest.raises(InvalidResumeError, match="archived"):
            resume.update_contact_info(contact)

    def test_update_raw_text_raises_on_archived(self, resume, raw_text):
        resume.archive()
        with pytest.raises(InvalidResumeError, match="archived"):
            resume.update_raw_text(raw_text)


# ============================================================
# Repr
# ============================================================


class TestRepr:
    def test_repr_contains_key_fields(self, resume):
        r = repr(resume)
        assert "resume-001" in r
        assert "DRAFT" in r
