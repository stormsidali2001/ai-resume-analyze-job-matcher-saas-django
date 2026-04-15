"""
domain/resume/services.py

Domain services for the Resume bounded context.
These are stateless operations that don't naturally fit inside the aggregate.
No external dependencies — pure Python only.
"""

from __future__ import annotations

from domain.common.value_objects import Skill
from domain.resume.aggregate import ResumeAggregate

# Default proficiency assigned when a skill is detected via keyword scan
_DEFAULT_PROFICIENCY = "intermediate"
_DEFAULT_CATEGORY = "general"


class ResumeAnalysisService:
    """
    Rule-based resume analysis service.

    Responsibilities:
        - Extract skills from raw resume text via keyword matching
        - Enrich a ResumeAggregate with extracted skills

    This is intentionally simple for Phase 1. Phase 2 will wire in LangChain
    for AI-powered extraction while keeping this domain service as a fallback.
    """

    def extract_skills_from_text(
        self,
        text: str,
        known_skills: list[str],
        category: str = _DEFAULT_CATEGORY,
        proficiency_level: str = _DEFAULT_PROFICIENCY,
    ) -> list[Skill]:
        """
        Scan `text` for occurrences of `known_skills` (case-insensitive).

        Returns a deduplicated list of Skill value objects for every keyword
        found in the text.

        Args:
            text: Raw resume text to scan.
            known_skills: Skill keyword list to look for (e.g. ["Python", "Django"]).
            category: Category assigned to all matched skills.
            proficiency_level: Proficiency assigned to all matched skills.

        Returns:
            List of unique Skill VOs found in the text.
        """
        if not text or not known_skills:
            return []

        text_lower = text.lower()
        found: list[Skill] = []
        seen_names: set[str] = set()

        for keyword in known_skills:
            normalised = keyword.strip().lower()
            if not normalised:
                continue
            if normalised in seen_names:
                continue
            if normalised in text_lower:
                found.append(
                    Skill(
                        name=keyword.strip(),
                        category=category,
                        proficiency_level=proficiency_level,
                    )
                )
                seen_names.add(normalised)

        return found

    def enrich_resume(
        self,
        resume: ResumeAggregate,
        extracted_skills: list[Skill],
    ) -> None:
        """
        Add extracted skills to a resume, silently skipping duplicates.

        This mirrors the real-world flow where AI extraction may propose
        skills the user already manually added.

        Args:
            resume: The aggregate to enrich (mutated in place).
            extracted_skills: Skills produced by extract_skills_from_text.
        """
        from domain.resume.exceptions import DuplicateSkillError  # avoid circular

        for skill in extracted_skills:
            try:
                resume.add_skill(skill)
            except DuplicateSkillError:
                # Silently skip — idempotent enrichment is intentional
                pass
