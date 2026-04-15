"""
domain/matching/services.py

ResumeJobMatchingService — pure business logic for scoring a resume
against a job posting. No AI, no external calls. Deterministic.

Scoring model (total: 100 points):
    - Skill overlap  : 60 pts  (matched required skills / total required skills)
    - Experience     : 30 pts  (candidate months / required months, capped at 1.0)
    - Base/contact   : 10 pts  (always awarded when resume has contact info)

Gaps and suggestions are generated from the scoring breakdown.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from domain.common.value_objects import Gap, ImprovementSuggestion, MatchScore, Skill
from domain.job.aggregate import JobAggregate
from domain.matching.aggregate import MatchResult
from domain.resume.aggregate import ResumeAggregate

_SKILL_WEIGHT = 60
_EXPERIENCE_WEIGHT = 30
_BASE_WEIGHT = 10


class ResumeJobMatchingService:
    """
    Stateless domain service that computes a MatchResult for a
    (resume, job) pair using deterministic rule-based scoring.

    This service enforces the core matching invariants:
        - Score is always in [0, 100]
        - Every missing required skill becomes a Gap
        - Experience shortfalls become a Gap with a suggestion
    """

    def calculate_match(
        self,
        resume: ResumeAggregate,
        job: JobAggregate,
        match_id: str | None = None,
    ) -> MatchResult:
        """
        Compute the match between a candidate's resume and a job posting.

        Args:
            resume: The candidate's ResumeAggregate.
            job: The JobAggregate to match against.
            match_id: Optional explicit ID (generated via uuid4 if omitted).

        Returns:
            A MatchResult aggregate with score, gaps, and suggestions.
        """
        _match_id = match_id or str(uuid.uuid4())
        gaps: list[Gap] = []
        suggestions: list[ImprovementSuggestion] = []

        # ── 1. Skill overlap score (0–60) ─────────────────────────────
        skill_score, skill_gaps, skill_suggestions = self._score_skills(
            resume.skills, job.required_skills
        )
        gaps.extend(skill_gaps)
        suggestions.extend(skill_suggestions)

        # ── 2. Experience score (0–30) ────────────────────────────────
        exp_score, exp_gaps, exp_suggestions = self._score_experience(
            resume.total_experience_months, job.required_experience_months
        )
        gaps.extend(exp_gaps)
        suggestions.extend(exp_suggestions)

        # ── 3. Base/contact score (0–10) ──────────────────────────────
        base_score = self._score_base(resume)

        # ── 4. Total ─────────────────────────────────────────────────
        total = skill_score + exp_score + base_score
        # Safety clamp — should never be needed but guarantees domain invariant
        total = max(0, min(100, total))

        return MatchResult.create(
            match_id=_match_id,
            resume_id=resume.resume_id,
            job_id=job.job_id,
            score=MatchScore(value=total),
            gaps=gaps,
            suggestions=suggestions,
        )

    # ------------------------------------------------------------------
    # Private scoring helpers
    # ------------------------------------------------------------------

    def _score_skills(
        self,
        candidate_skills: list[Skill],
        required_skills: list[Skill],
    ) -> tuple[int, list[Gap], list[ImprovementSuggestion]]:
        """Returns (score 0-60, gaps, suggestions)."""
        if not required_skills:
            # No skills required → full marks, no gaps
            return _SKILL_WEIGHT, [], []

        matched = 0
        gaps: list[Gap] = []
        suggestions: list[ImprovementSuggestion] = []

        for req_skill in required_skills:
            if any(cs.matches(req_skill) for cs in candidate_skills):
                matched += 1
            else:
                gaps.append(
                    Gap(
                        gap_type="missing_skill",
                        description=(
                            f"Required skill '{req_skill.name}' "
                            f"(category: {req_skill.category}) is not on your resume."
                        ),
                    )
                )
                suggestions.append(
                    ImprovementSuggestion(
                        text=(
                            f"Add '{req_skill.name}' to your skills. "
                            f"Consider online courses or personal projects to "
                            f"demonstrate this capability."
                        ),
                        priority="high",
                        category="skills",
                    )
                )

        ratio = matched / len(required_skills)
        score = round(ratio * _SKILL_WEIGHT)
        return score, gaps, suggestions

    def _score_experience(
        self,
        candidate_months: int,
        required_months: int,
    ) -> tuple[int, list[Gap], list[ImprovementSuggestion]]:
        """Returns (score 0-30, gaps, suggestions)."""
        if required_months <= 0:
            # No experience requirement → full marks
            return _EXPERIENCE_WEIGHT, [], []

        ratio = min(candidate_months / required_months, 1.0)
        score = round(ratio * _EXPERIENCE_WEIGHT)
        gaps: list[Gap] = []
        suggestions: list[ImprovementSuggestion] = []

        if candidate_months < required_months:
            shortfall = required_months - candidate_months
            years_short = round(shortfall / 12, 1)
            gaps.append(
                Gap(
                    gap_type="experience_shortfall",
                    description=(
                        f"Job requires {required_months} months of experience; "
                        f"your resume shows {candidate_months} months "
                        f"(shortfall: ~{years_short} years)."
                    ),
                )
            )
            suggestions.append(
                ImprovementSuggestion(
                    text=(
                        f"You are approximately {years_short} year(s) short on "
                        f"required experience. Highlight any freelance, open-source, "
                        f"or project work that demonstrates relevant hands-on time."
                    ),
                    priority="medium",
                    category="experience",
                )
            )

        return score, gaps, suggestions

    def _score_base(self, resume: ResumeAggregate) -> int:
        """10 points if the resume has complete contact information."""
        ci = resume.contact_info
        if ci.email and ci.phone and ci.location:
            return _BASE_WEIGHT
        return 0
