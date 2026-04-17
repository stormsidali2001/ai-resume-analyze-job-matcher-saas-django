"""
domain/matching/services.py

ResumeJobMatchingService — pure business logic for scoring a resume
against a job posting. No AI, no external calls. Deterministic.

Scoring model (total: 100 points):
    - Skill overlap  : 60 pts  (weighted by category importance + proficiency match)
    - Experience     : 30 pts  (candidate months / required months, capped at 1.0)
    - Base/contact   : 10 pts  (always awarded when resume has complete contact info)

Skill weighting:
    Each required skill contributes a weight based on its category
    (language=3.0 down to methodology=0.5). When the candidate has the skill
    but at a lower proficiency than required, partial credit is awarded via
    a proficiency multiplier (1.0 → 0.75 → 0.40 → 0.10 for each level short).

Gap types:
    - missing_skill    : required skill absent from resume entirely
    - proficiency_gap  : skill present but candidate level is below required
    - experience_shortfall : not enough total months of experience
"""

from __future__ import annotations

import uuid
from datetime import datetime

from domain.common.skill_categories import CATEGORY_SCORE_WEIGHT, DEFAULT_WEIGHT
from domain.common.value_objects import Gap, ImprovementSuggestion, MatchScore, Skill
from domain.job.aggregate import JobAggregate
from domain.matching.aggregate import MatchResult
from domain.resume.aggregate import ResumeAggregate

_SKILL_WEIGHT = 60
_EXPERIENCE_WEIGHT = 30
_BASE_WEIGHT = 10

# Proficiency levels as ordinal values for comparison
_PROFICIENCY_ORDER: dict[str, int] = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
    "expert": 3,
}


def _proficiency_multiplier(required: str, candidate: str) -> float:
    """
    Returns a score multiplier (0-1) based on how the candidate's proficiency
    compares to the required level for a skill.

    Meeting or exceeding the requirement → 1.0 (full credit).
    Each level short reduces credit substantially.
    """
    diff = _PROFICIENCY_ORDER.get(required, 1) - _PROFICIENCY_ORDER.get(candidate, 1)
    if diff <= 0:
        return 1.0   # meets or exceeds requirement
    if diff == 1:
        return 0.75  # one level short (e.g. advanced required, intermediate has)
    if diff == 2:
        return 0.40  # two levels short
    return 0.10      # three levels short (beginner when expert needed)


def _gap_priority(category: str) -> str:
    """
    Derive suggestion priority from the category's score weight.
    High-weight categories (languages, frameworks) produce high-priority gaps.
    """
    weight = CATEGORY_SCORE_WEIGHT.get(category, DEFAULT_WEIGHT)
    if weight >= 2.5:
        return "high"    # language, framework
    if weight >= 1.5:
        return "medium"  # database, cloud, devops, architecture, data-science
    return "low"          # tooling, testing, methodology


class ResumeJobMatchingService:
    """
    Stateless domain service that computes a MatchResult for a
    (resume, job) pair using deterministic rule-based scoring.

    This service enforces the core matching invariants:
        - Score is always in [0, 100]
        - Every missing required skill becomes a Gap
        - Skills present at a lower proficiency than required become a proficiency_gap
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

        # ── 1. Skill overlap score (0–60, weighted) ───────────────────
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
        """
        Returns (score 0-60, gaps, suggestions).

        Score is computed as a weighted ratio:
            earned_weight / total_weight * 60

        where each required skill contributes a category weight, and a matched
        skill is further scaled by the proficiency multiplier.
        """
        if not required_skills:
            return _SKILL_WEIGHT, [], []

        total_weight = sum(
            CATEGORY_SCORE_WEIGHT.get(s.category, DEFAULT_WEIGHT)
            for s in required_skills
        )
        earned_weight = 0.0
        gaps: list[Gap] = []
        suggestions: list[ImprovementSuggestion] = []

        for req in required_skills:
            cat_weight = CATEGORY_SCORE_WEIGHT.get(req.category, DEFAULT_WEIGHT)
            match = next((cs for cs in candidate_skills if cs.matches(req)), None)

            if match is None:
                # Skill entirely absent from resume
                gaps.append(Gap(
                    gap_type="missing_skill",
                    description=(
                        f"Required skill '{req.name}' "
                        f"(category: {req.category}) is not on your resume."
                    ),
                ))
                suggestions.append(ImprovementSuggestion(
                    text=(
                        f"Add '{req.name}' to your skills. "
                        f"Consider online courses or personal projects to "
                        f"demonstrate this capability."
                    ),
                    priority=_gap_priority(req.category),
                    category="skills",
                ))
            else:
                mult = _proficiency_multiplier(req.proficiency_level, match.proficiency_level)
                earned_weight += cat_weight * mult

                if mult < 1.0:
                    # Skill present but below required proficiency
                    gaps.append(Gap(
                        gap_type="proficiency_gap",
                        description=(
                            f"Your {req.name} level is {match.proficiency_level}; "
                            f"{req.proficiency_level} is required for this role."
                        ),
                    ))
                    suggestions.append(ImprovementSuggestion(
                        text=(
                            f"Deepen your {req.name} expertise from "
                            f"{match.proficiency_level} to {req.proficiency_level} "
                            f"through advanced projects, open-source contributions, "
                            f"or targeted certifications."
                        ),
                        priority="medium" if mult >= 0.75 else "high",
                        category="skills",
                    ))

        score = (
            round((earned_weight / total_weight) * _SKILL_WEIGHT)
            if total_weight > 0
            else _SKILL_WEIGHT
        )
        return score, gaps, suggestions

    def _score_experience(
        self,
        candidate_months: int,
        required_months: int,
    ) -> tuple[int, list[Gap], list[ImprovementSuggestion]]:
        """Returns (score 0-30, gaps, suggestions)."""
        if required_months <= 0:
            return _EXPERIENCE_WEIGHT, [], []

        ratio = min(candidate_months / required_months, 1.0)
        score = round(ratio * _EXPERIENCE_WEIGHT)
        gaps: list[Gap] = []
        suggestions: list[ImprovementSuggestion] = []

        if candidate_months < required_months:
            shortfall = required_months - candidate_months
            years_short = round(shortfall / 12, 1)
            gaps.append(Gap(
                gap_type="experience_shortfall",
                description=(
                    f"Job requires {required_months} months of experience; "
                    f"your resume shows {candidate_months} months "
                    f"(shortfall: ~{years_short} years)."
                ),
            ))
            suggestions.append(ImprovementSuggestion(
                text=(
                    f"You are approximately {years_short} year(s) short on "
                    f"required experience. Highlight any freelance, open-source, "
                    f"or project work that demonstrates relevant hands-on time."
                ),
                priority="medium",
                category="experience",
            ))

        return score, gaps, suggestions

    def _score_base(self, resume: ResumeAggregate) -> int:
        """10 points if the resume has complete contact information."""
        ci = resume.contact_info
        if ci.email and ci.phone and ci.location:
            return _BASE_WEIGHT
        return 0
