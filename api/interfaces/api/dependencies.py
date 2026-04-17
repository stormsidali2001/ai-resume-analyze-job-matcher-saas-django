"""
interfaces/api/dependencies.py

Simple factory functions that wire up use cases with their concrete dependencies.
"""

from __future__ import annotations

from application.user.use_cases import CreateUserUseCase
from application.job.use_cases import (
    AddRequiredSkillToJobUseCase,
    CloseJobUseCase,
    CreateJobUseCase,
    GetJobUseCase,
    ListPublishedJobsUseCase,
    ListRecruiterJobsUseCase,
    PublishJobUseCase,
)
from application.matching.use_cases import MatchResumeToJobUseCase
from application.resume.ports import FileParserPort
from application.resume.use_cases import (
    AddSkillToResumeUseCase,
    AnalyzeResumeUseCase,
    ArchiveResumeUseCase,
    CreateResumeUseCase,
    GetResumeUseCase,
    ListCandidateResumesUseCase,
    UpdateResumeTextUseCase,
)
from django.conf import settings

from domain.matching.services import ResumeJobMatchingService
from domain.resume.services import ResumeAnalysisService
from infrastructure.ai.gemini_resume_parser import GeminiResumeParser
from infrastructure.files.pdf_parser import PdfFileParser
from infrastructure.repositories.job import DjangoJobRepository
from infrastructure.repositories.resume import DjangoResumeRepository
from infrastructure.repositories.user import DjangoUserRepository


def get_user_use_cases() -> dict:
    repo = DjangoUserRepository()
    return {
        "create": CreateUserUseCase(repo),
    }


def get_resume_use_cases() -> dict:
    repo = DjangoResumeRepository()
    service = ResumeAnalysisService()
    ai_parser = (
        GeminiResumeParser(api_key=settings.GEMINI_API_KEY)
        if settings.GEMINI_API_KEY
        else None
    )
    return {
        "create": CreateResumeUseCase(repo, service, ai_parser=ai_parser),
        "get": GetResumeUseCase(repo),
        "list": ListCandidateResumesUseCase(repo),
        "update_text": UpdateResumeTextUseCase(repo),
        "analyze": AnalyzeResumeUseCase(repo, service, ai_parser=ai_parser),
        "add_skill": AddSkillToResumeUseCase(repo),
        "archive": ArchiveResumeUseCase(repo),
    }


def get_job_use_cases() -> dict:
    repo = DjangoJobRepository()
    return {
        "create": CreateJobUseCase(repo),
        "get": GetJobUseCase(repo),
        "list_published": ListPublishedJobsUseCase(repo),
        "list_mine": ListRecruiterJobsUseCase(repo),
        "publish": PublishJobUseCase(repo),
        "close": CloseJobUseCase(repo),
        "add_skill": AddRequiredSkillToJobUseCase(repo),
    }


def get_file_parser() -> FileParserPort:
    return PdfFileParser()


def get_match_use_case() -> MatchResumeToJobUseCase:
    return MatchResumeToJobUseCase(
        DjangoResumeRepository(),
        DjangoJobRepository(),
        ResumeJobMatchingService(),
    )
