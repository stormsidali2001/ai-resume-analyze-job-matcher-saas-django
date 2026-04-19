"""
application/resume/use_cases.py

One class per use case, each with a single execute() method.
Use cases are thin orchestrators: they fetch aggregates, invoke domain
methods, persist, and map to DTOs. Zero business logic lives here.
"""

from __future__ import annotations

import uuid

from application.common.exceptions import AIAnalysisError, NotFoundError, UnauthorizedError
from application.resume.dtos import (
    AnalyzeResumeCommand,
    AddSkillCommand,
    ContactInfoDTO,
    CreateResumeCommand,
    EducationDTO,
    ExperienceDTO,
    ResumeDTO,
    SkillDTO,
    UpdateResumeTextCommand,
)
from domain.common.value_objects import Skill
from domain.resume.aggregate import ResumeAggregate
from domain.resume.exceptions import ResumeNotFoundError
from domain.resume.repositories import ResumeRepository
from domain.resume.services import ResumeAnalysisService
from domain.resume.value_objects import ContactInfo, Education, Experience, RawResumeContent

from application.resume.ports import AIAnalysisPort


# ---------------------------------------------------------------------------
# Shared mapper
# ---------------------------------------------------------------------------


def _resume_to_dto(resume: ResumeAggregate) -> ResumeDTO:
    return ResumeDTO(
        resume_id=resume.resume_id,
        candidate_id=resume.candidate_id,
        status=resume.status,
        analysis_status=resume.analysis_status,
        raw_text_preview=resume.raw_text.preview,
        contact_info=ContactInfoDTO(
            email=resume.contact_info.email,
            phone=resume.contact_info.phone,
            location=resume.contact_info.location,
        ),
        skills=[
            SkillDTO(
                name=s.name,
                category=s.category,
                proficiency_level=s.proficiency_level,
            )
            for s in resume.skills
        ],
        experiences=[
            ExperienceDTO(
                role=e.role,
                company=e.company,
                duration_months=e.duration_months,
                responsibilities=list(e.responsibilities),
            )
            for e in resume.experiences
        ],
        education=[
            EducationDTO(
                degree=edu.degree,
                institution=edu.institution,
                graduation_year=edu.graduation_year,
            )
            for edu in resume.education
        ],
        total_experience_months=resume.total_experience_months,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


def _fetch_and_authorize(
    repo: ResumeRepository,
    resume_id: str,
    requester_id: str,
) -> ResumeAggregate:
    """Fetch resume and verify ownership. Raises NotFoundError / UnauthorizedError."""
    try:
        resume = repo.get_by_id(resume_id)
    except ResumeNotFoundError:
        raise NotFoundError("Resume", resume_id)
    if resume.candidate_id != requester_id:
        raise UnauthorizedError("Resume", resume_id)
    return resume


# ---------------------------------------------------------------------------
# Use Cases
# ---------------------------------------------------------------------------


class CreateResumeUseCase:
    """
    Create a new resume for a candidate and immediately analyze it.

    When an AIAnalysisPort is available it performs a full AI parse
    (skills + experiences + education). When no parser is configured it
    falls back to the rule-based ResumeAnalysisService for basic skill
    extraction from the raw text.
    """

    def __init__(
        self,
        repo: ResumeRepository,
        analysis_service: ResumeAnalysisService,
        ai_parser: AIAnalysisPort | None = None,
    ) -> None:
        self._repo = repo
        self._service = analysis_service
        self._ai_parser = ai_parser

    def execute(self, cmd: CreateResumeCommand) -> ResumeDTO:
        resume = ResumeAggregate(
            resume_id=str(uuid.uuid4()),
            candidate_id=cmd.candidate_id,
            raw_text=RawResumeContent(text=cmd.raw_text),
            contact_info=ContactInfo(
                email=cmd.email,
                phone=cmd.phone,
                location=cmd.location,
            ),
        )

        if self._ai_parser is not None:
            try:
                parsed = self._ai_parser.parse(resume.raw_text.text)
            except Exception as exc:
                raise AIAnalysisError(str(exc)) from exc

            skills = [
                Skill(
                    name=s.name,
                    category=s.category,
                    proficiency_level=s.proficiency_level,
                )
                for s in parsed.skills
            ]
            experiences = [
                Experience(
                    role=e.role,
                    company=e.company,
                    duration_months=e.duration_months,
                    responsibilities=tuple(e.responsibilities),
                )
                for e in parsed.experiences
            ]
            education = [
                Education(
                    degree=ed.degree,
                    institution=ed.institution,
                    graduation_year=ed.graduation_year,
                )
                for ed in parsed.education
            ]
            resume.update_from_parsed_text(skills, experiences, education)
        else:
            extracted = self._service.extract_skills_from_text(
                text=resume.raw_text.text,
                known_skills=[],
            )
            self._service.enrich_resume(resume, extracted)

        self._repo.save(resume)
        return _resume_to_dto(resume)


class GetResumeUseCase:
    """Fetch a resume by ID, enforcing candidate ownership."""

    def __init__(self, repo: ResumeRepository) -> None:
        self._repo = repo

    def execute(self, resume_id: str, requester_id: str) -> ResumeDTO:
        resume = _fetch_and_authorize(self._repo, resume_id, requester_id)
        return _resume_to_dto(resume)


class ListCandidateResumesUseCase:
    """Return all resumes belonging to a candidate."""

    def __init__(self, repo: ResumeRepository) -> None:
        self._repo = repo

    def execute(self, candidate_id: str) -> list[ResumeDTO]:
        resumes = self._repo.list_by_candidate(candidate_id)
        return [_resume_to_dto(r) for r in resumes]


class UpdateResumeTextUseCase:
    """Replace the raw text on an existing resume."""

    def __init__(self, repo: ResumeRepository) -> None:
        self._repo = repo

    def execute(self, cmd: UpdateResumeTextCommand) -> ResumeDTO:
        resume = _fetch_and_authorize(self._repo, cmd.resume_id, cmd.candidate_id)
        resume.update_raw_text(RawResumeContent(text=cmd.new_raw_text))
        self._repo.save(resume)
        return _resume_to_dto(resume)


class AnalyzeResumeUseCase:
    """
    Analyze a resume's raw text to extract structured data.

    When an AIAnalysisPort is provided (Gemini / LangChain), it performs a
    full parse that bulk-replaces skills, experiences, and education on the
    aggregate. Without a parser it falls back to the rule-based keyword scan
    which additively enriches skills only.
    """

    def __init__(
        self,
        repo: ResumeRepository,
        analysis_service: ResumeAnalysisService,
        ai_parser: AIAnalysisPort | None = None,
    ) -> None:
        self._repo = repo
        self._service = analysis_service
        self._ai_parser = ai_parser

    def execute(self, cmd: AnalyzeResumeCommand) -> ResumeDTO:
        resume = _fetch_and_authorize(self._repo, cmd.resume_id, cmd.candidate_id)

        if self._ai_parser is not None:
            try:
                parsed = self._ai_parser.parse(resume.raw_text.text)
            except Exception as exc:
                raise AIAnalysisError(str(exc)) from exc

            skills = [
                Skill(
                    name=s.name,
                    category=s.category,
                    proficiency_level=s.proficiency_level,
                )
                for s in parsed.skills
            ]
            experiences = [
                Experience(
                    role=e.role,
                    company=e.company,
                    duration_months=e.duration_months,
                    responsibilities=tuple(e.responsibilities),
                )
                for e in parsed.experiences
            ]
            education = [
                Education(
                    degree=ed.degree,
                    institution=ed.institution,
                    graduation_year=ed.graduation_year,
                )
                for ed in parsed.education
            ]
            resume.update_from_parsed_text(skills, experiences, education)
        else:
            extracted = self._service.extract_skills_from_text(
                text=resume.raw_text.text,
                known_skills=cmd.known_skills,
            )
            self._service.enrich_resume(resume, extracted)

        self._repo.save(resume)
        return _resume_to_dto(resume)


class AddSkillToResumeUseCase:
    """Manually add a skill to a resume."""

    def __init__(self, repo: ResumeRepository) -> None:
        self._repo = repo

    def execute(self, cmd: AddSkillCommand) -> ResumeDTO:
        resume = _fetch_and_authorize(self._repo, cmd.resume_id, cmd.candidate_id)
        skill = Skill(
            name=cmd.name,
            category=cmd.category,
            proficiency_level=cmd.proficiency_level,
        )
        resume.add_skill(skill)
        self._repo.save(resume)
        return _resume_to_dto(resume)


class ArchiveResumeUseCase:
    """Archive a resume so it can no longer be modified."""

    def __init__(self, repo: ResumeRepository) -> None:
        self._repo = repo

    def execute(self, resume_id: str, requester_id: str) -> None:
        resume = _fetch_and_authorize(self._repo, resume_id, requester_id)
        resume.archive()
        self._repo.save(resume)
