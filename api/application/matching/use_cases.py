"""
application/matching/use_cases.py

Use case for matching a resume against a job posting.
"""

from __future__ import annotations

from application.common.exceptions import NotFoundError, UnauthorizedError
from application.matching.dtos import GapDTO, MatchRequestCommand, MatchResultDTO, SuggestionDTO
from domain.job.exceptions import JobNotFoundError
from domain.job.repositories import JobRepository
from domain.matching.services import ResumeJobMatchingService
from domain.resume.exceptions import ResumeNotFoundError
from domain.resume.repositories import ResumeRepository


class MatchResumeToJobUseCase:
    """
    Orchestrate the match between a candidate's resume and a job posting.

    Flow:
        1. Fetch resume + verify candidate ownership
        2. Fetch job (public — no ownership check on job)
        3. Delegate scoring to ResumeJobMatchingService
        4. Map domain MatchResult → MatchResultDTO
    """

    def __init__(
        self,
        resume_repo: ResumeRepository,
        job_repo: JobRepository,
        matching_service: ResumeJobMatchingService,
    ) -> None:
        self._resume_repo = resume_repo
        self._job_repo = job_repo
        self._service = matching_service

    def execute(self, cmd: MatchRequestCommand) -> MatchResultDTO:
        # 1. Resume + ownership
        try:
            resume = self._resume_repo.get_by_id(cmd.resume_id)
        except ResumeNotFoundError:
            raise NotFoundError("Resume", cmd.resume_id)
        if resume.candidate_id != cmd.candidate_id:
            raise UnauthorizedError("Resume", cmd.resume_id)

        # 2. Job (public)
        try:
            job = self._job_repo.get_by_id(cmd.job_id)
        except JobNotFoundError:
            raise NotFoundError("Job", cmd.job_id)

        # 3. Score
        result = self._service.calculate_match(resume, job)

        # 4. Map → DTO
        return MatchResultDTO(
            match_id=result.match_id,
            resume_id=result.resume_id,
            job_id=result.job_id,
            score=result.score.value,
            score_label=result.score.label,
            gaps=[GapDTO(gap_type=g.gap_type, description=g.description) for g in result.gaps],
            suggestions=[
                SuggestionDTO(text=s.text, priority=s.priority, category=s.category)
                for s in result.suggestions
            ],
            calculated_at=result.calculated_at,
        )
