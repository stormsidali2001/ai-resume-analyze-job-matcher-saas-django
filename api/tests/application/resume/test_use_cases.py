"""
tests/application/resume/test_use_cases.py

Unit tests for all resume use cases with mocked repositories.
Pattern: arrange (mock repo + domain objects) → act (execute) → assert (DTO + repo calls).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from application.common.exceptions import AIAnalysisError, NotFoundError, UnauthorizedError
from application.resume.dtos import (
    AddSkillCommand,
    AnalyzeResumeCommand,
    CreateResumeCommand,
    EducationDTO,
    ExperienceDTO,
    ParsedResumeData,
    SkillDTO,
    UpdateResumeTextCommand,
)
from application.resume.use_cases import (
    AddSkillToResumeUseCase,
    AnalyzeResumeUseCase,
    ArchiveResumeUseCase,
    CreateResumeUseCase,
    GetResumeUseCase,
    ListCandidateResumesUseCase,
    UpdateResumeTextUseCase,
)
from domain.common.value_objects import Skill
from domain.resume.aggregate import ResumeAggregate
from domain.resume.exceptions import ResumeNotFoundError
from domain.resume.services import ResumeAnalysisService
from domain.resume.value_objects import ContactInfo, RawResumeContent


# ============================================================
# Helpers
# ============================================================

_RAW = "Senior Python engineer with 7 years of experience in distributed systems."
_CONTACT = ContactInfo(email="a@b.com", phone="+1-000", location="NYC")
_LONG_TEXT = _RAW * 3  # well beyond 50-char minimum


def _make_resume(
    resume_id: str = "r1",
    candidate_id: str = "c1",
    skills: list[Skill] | None = None,
) -> ResumeAggregate:
    r = ResumeAggregate(
        resume_id=resume_id,
        candidate_id=candidate_id,
        raw_text=RawResumeContent(text=_LONG_TEXT),
        contact_info=_CONTACT,
    )
    for s in (skills or []):
        r.add_skill(s)
    return r


def _mock_repo(resume: ResumeAggregate | None = None) -> MagicMock:
    repo = MagicMock()
    if resume is not None:
        repo.get_by_id.return_value = resume
    else:
        repo.get_by_id.side_effect = ResumeNotFoundError("not found")
    repo.list_by_candidate.return_value = [resume] if resume else []
    return repo


# ============================================================
# CreateResumeUseCase
# ============================================================


class TestCreateResumeUseCase:
    def _cmd(self, **overrides) -> CreateResumeCommand:
        defaults = dict(
            candidate_id="c1",
            raw_text=_LONG_TEXT,
            email="a@b.com",
            phone="+1-000",
            location="NYC",
        )
        defaults.update(overrides)
        return CreateResumeCommand(**defaults)

    def _uc(self, repo=None, ai_parser=None):
        return CreateResumeUseCase(
            repo or MagicMock(),
            ResumeAnalysisService(),
            ai_parser=ai_parser,
        )

    def test_returns_resume_dto(self):
        dto = self._uc().execute(self._cmd())
        assert dto.candidate_id == "c1"
        assert dto.status == "DRAFT"

    def test_repo_save_called_once(self):
        repo = MagicMock()
        self._uc(repo).execute(self._cmd())
        repo.save.assert_called_once()

    def test_generated_resume_id_is_nonempty(self):
        dto = self._uc().execute(self._cmd())
        assert dto.resume_id and len(dto.resume_id) > 0

    def test_contact_info_mapped_correctly(self):
        dto = self._uc().execute(self._cmd(email="x@y.com"))
        assert dto.contact_info.email == "x@y.com"

    def test_ai_parser_populates_skills_on_create(self):
        repo = MagicMock()
        parsed = ParsedResumeData(
            skills=[SkillDTO(name="Python", category="programming", proficiency_level="expert")],
            experiences=[],
            education=[],
        )
        ai_parser = MagicMock()
        ai_parser.parse.return_value = parsed

        dto = self._uc(repo, ai_parser=ai_parser).execute(self._cmd())

        ai_parser.parse.assert_called_once()
        assert len(dto.skills) == 1
        assert dto.skills[0].name == "Python"

    def test_ai_parser_error_raises_ai_analysis_error_on_create(self):
        ai_parser = MagicMock()
        ai_parser.parse.side_effect = RuntimeError("quota exceeded")

        with pytest.raises(AIAnalysisError):
            self._uc(ai_parser=ai_parser).execute(self._cmd())

    def test_no_ai_parser_falls_back_to_rule_based(self):
        dto = self._uc(ai_parser=None).execute(self._cmd())
        # rule-based with empty known_skills → no skills extracted, but no crash
        assert isinstance(dto.skills, list)


# ============================================================
# GetResumeUseCase
# ============================================================


class TestGetResumeUseCase:
    def test_returns_dto_for_owner(self):
        resume = _make_resume(resume_id="r1", candidate_id="c1")
        repo = _mock_repo(resume)
        dto = GetResumeUseCase(repo).execute("r1", "c1")
        assert dto.resume_id == "r1"

    def test_raises_not_found(self):
        repo = _mock_repo(None)
        with pytest.raises(NotFoundError):
            GetResumeUseCase(repo).execute("missing", "c1")

    def test_raises_unauthorized_for_wrong_candidate(self):
        resume = _make_resume(candidate_id="c1")
        repo = _mock_repo(resume)
        with pytest.raises(UnauthorizedError):
            GetResumeUseCase(repo).execute("r1", "c-other")

    def test_repo_save_never_called(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        GetResumeUseCase(repo).execute("r1", "c1")
        repo.save.assert_not_called()


# ============================================================
# ListCandidateResumesUseCase
# ============================================================


class TestListCandidateResumesUseCase:
    def test_returns_list_of_dtos(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        dtos = ListCandidateResumesUseCase(repo).execute("c1")
        assert len(dtos) == 1
        assert dtos[0].candidate_id == "c1"

    def test_empty_list_when_no_resumes(self):
        repo = MagicMock()
        repo.list_by_candidate.return_value = []
        dtos = ListCandidateResumesUseCase(repo).execute("c1")
        assert dtos == []

    def test_repo_save_never_called(self):
        repo = MagicMock()
        repo.list_by_candidate.return_value = []
        ListCandidateResumesUseCase(repo).execute("c1")
        repo.save.assert_not_called()


# ============================================================
# UpdateResumeTextUseCase
# ============================================================


class TestUpdateResumeTextUseCase:
    def test_updates_raw_text_and_returns_dto(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        new_text = "Completely new resume content for a Python developer. " * 5
        cmd = UpdateResumeTextCommand(resume_id="r1", candidate_id="c1", new_raw_text=new_text)
        dto = UpdateResumeTextUseCase(repo).execute(cmd)
        assert new_text[:120].strip() in dto.raw_text_preview

    def test_repo_save_called(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        cmd = UpdateResumeTextCommand(resume_id="r1", candidate_id="c1", new_raw_text=_LONG_TEXT)
        UpdateResumeTextUseCase(repo).execute(cmd)
        repo.save.assert_called_once()

    def test_raises_not_found(self):
        repo = _mock_repo(None)
        cmd = UpdateResumeTextCommand(resume_id="r1", candidate_id="c1", new_raw_text=_LONG_TEXT)
        with pytest.raises(NotFoundError):
            UpdateResumeTextUseCase(repo).execute(cmd)

    def test_raises_unauthorized(self):
        resume = _make_resume(candidate_id="c1")
        repo = _mock_repo(resume)
        cmd = UpdateResumeTextCommand(resume_id="r1", candidate_id="other", new_raw_text=_LONG_TEXT)
        with pytest.raises(UnauthorizedError):
            UpdateResumeTextUseCase(repo).execute(cmd)


# ============================================================
# AnalyzeResumeUseCase
# ============================================================


class TestAnalyzeResumeUseCase:
    def test_extracts_and_enriches_skills(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        service = ResumeAnalysisService()
        cmd = AnalyzeResumeCommand(
            resume_id="r1",
            candidate_id="c1",
            known_skills=["Python", "Django"],
        )
        # raw text contains "Python" and "Django" → both extracted
        resume._raw_text = RawResumeContent(
            text="Python developer with Django experience in REST APIs. " * 3
        )
        dto = AnalyzeResumeUseCase(repo, service).execute(cmd)
        skill_names = [s.name for s in dto.skills]
        assert "Python" in skill_names
        assert "Django" in skill_names

    def test_repo_save_called(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        service = MagicMock(spec=ResumeAnalysisService)
        service.extract_skills_from_text.return_value = []
        cmd = AnalyzeResumeCommand(resume_id="r1", candidate_id="c1", known_skills=[])
        AnalyzeResumeUseCase(repo, service).execute(cmd)
        repo.save.assert_called_once()

    def test_raises_unauthorized(self):
        resume = _make_resume(candidate_id="c1")
        repo = _mock_repo(resume)
        service = MagicMock(spec=ResumeAnalysisService)
        cmd = AnalyzeResumeCommand(resume_id="r1", candidate_id="wrong", known_skills=[])
        with pytest.raises(UnauthorizedError):
            AnalyzeResumeUseCase(repo, service).execute(cmd)

    # -- AI parser path --

    def test_ai_parser_replaces_skills_experiences_education(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        service = MagicMock(spec=ResumeAnalysisService)

        parsed = ParsedResumeData(
            skills=[SkillDTO(name="Python", category="programming", proficiency_level="expert")],
            experiences=[
                ExperienceDTO(
                    role="Engineer",
                    company="Acme",
                    duration_months=24,
                    responsibilities=["Built APIs"],
                )
            ],
            education=[
                EducationDTO(degree="BSc CS", institution="MIT", graduation_year=2019)
            ],
        )
        ai_parser = MagicMock()
        ai_parser.parse.return_value = parsed

        cmd = AnalyzeResumeCommand(resume_id="r1", candidate_id="c1", known_skills=[])
        dto = AnalyzeResumeUseCase(repo, service, ai_parser=ai_parser).execute(cmd)

        # AI path: rule-based service should NOT be called
        service.extract_skills_from_text.assert_not_called()
        service.enrich_resume.assert_not_called()

        assert len(dto.skills) == 1
        assert dto.skills[0].name == "Python"
        assert len(dto.experiences) == 1
        assert dto.experiences[0].role == "Engineer"
        assert len(dto.education) == 1
        assert dto.education[0].degree == "BSc CS"

    def test_ai_parser_wraps_exception_in_ai_analysis_error(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        service = MagicMock(spec=ResumeAnalysisService)

        ai_parser = MagicMock()
        ai_parser.parse.side_effect = RuntimeError("Gemini quota exceeded")

        cmd = AnalyzeResumeCommand(resume_id="r1", candidate_id="c1", known_skills=[])
        with pytest.raises(AIAnalysisError, match="Gemini quota exceeded"):
            AnalyzeResumeUseCase(repo, service, ai_parser=ai_parser).execute(cmd)

    def test_no_ai_parser_falls_back_to_rule_based(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        service = MagicMock(spec=ResumeAnalysisService)
        service.extract_skills_from_text.return_value = []

        cmd = AnalyzeResumeCommand(resume_id="r1", candidate_id="c1", known_skills=["Python"])
        AnalyzeResumeUseCase(repo, service, ai_parser=None).execute(cmd)

        service.extract_skills_from_text.assert_called_once()
        service.enrich_resume.assert_called_once()

    def test_ai_parser_repo_save_called(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        service = MagicMock(spec=ResumeAnalysisService)

        ai_parser = MagicMock()
        ai_parser.parse.return_value = ParsedResumeData(skills=[], experiences=[], education=[])

        cmd = AnalyzeResumeCommand(resume_id="r1", candidate_id="c1", known_skills=[])
        AnalyzeResumeUseCase(repo, service, ai_parser=ai_parser).execute(cmd)
        repo.save.assert_called_once()


# ============================================================
# AddSkillToResumeUseCase
# ============================================================


class TestAddSkillToResumeUseCase:
    def test_adds_skill_and_returns_dto(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        cmd = AddSkillCommand(
            resume_id="r1",
            candidate_id="c1",
            name="Python",
            category="programming",
            proficiency_level="expert",
        )
        dto = AddSkillToResumeUseCase(repo).execute(cmd)
        assert any(s.name == "Python" for s in dto.skills)

    def test_repo_save_called(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        cmd = AddSkillCommand(
            resume_id="r1", candidate_id="c1",
            name="Go", category="programming", proficiency_level="intermediate",
        )
        AddSkillToResumeUseCase(repo).execute(cmd)
        repo.save.assert_called_once()

    def test_raises_unauthorized(self):
        resume = _make_resume(candidate_id="c1")
        repo = _mock_repo(resume)
        cmd = AddSkillCommand(
            resume_id="r1", candidate_id="other",
            name="Go", category="programming", proficiency_level="intermediate",
        )
        with pytest.raises(UnauthorizedError):
            AddSkillToResumeUseCase(repo).execute(cmd)


# ============================================================
# ArchiveResumeUseCase
# ============================================================


class TestArchiveResumeUseCase:
    def test_archives_resume(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        ArchiveResumeUseCase(repo).execute("r1", "c1")
        assert resume.status == "ARCHIVED"

    def test_returns_none(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        result = ArchiveResumeUseCase(repo).execute("r1", "c1")
        assert result is None

    def test_repo_save_called(self):
        resume = _make_resume()
        repo = _mock_repo(resume)
        ArchiveResumeUseCase(repo).execute("r1", "c1")
        repo.save.assert_called_once()

    def test_raises_not_found(self):
        repo = _mock_repo(None)
        with pytest.raises(NotFoundError):
            ArchiveResumeUseCase(repo).execute("missing", "c1")

    def test_raises_unauthorized(self):
        resume = _make_resume(candidate_id="c1")
        repo = _mock_repo(resume)
        with pytest.raises(UnauthorizedError):
            ArchiveResumeUseCase(repo).execute("r1", "wrong")
