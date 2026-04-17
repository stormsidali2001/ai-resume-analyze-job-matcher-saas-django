"""
infrastructure/ai/gemini_resume_parser.py

LangChain + Google Gemini implementation of AIAnalysisPort.
Sends the raw resume text to Gemini with structured output binding so the
model returns a validated Pydantic object directly — no manual JSON parsing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from application.resume.dtos import (
    EducationDTO,
    ExperienceDTO,
    ParsedResumeData,
    SkillDTO,
)
from application.resume.ports import AIAnalysisPort
from domain.common.skill_categories import CANONICAL_CATEGORIES


# ---------------------------------------------------------------------------
# Internal structured-output schemas (infrastructure-local, never exported)
# ---------------------------------------------------------------------------

# Literal type built from the canonical category tuple so Gemini's structured
# output is forced to pick one of the 10 valid categories.
_CategoryLiteral = Literal[
    "language", "framework", "database", "cloud", "devops",
    "architecture", "data-science", "tooling", "testing", "methodology",
]


class _SkillOut(BaseModel):
    name: str = Field(
        description=(
            "Canonical skill name, e.g. 'Python', 'PostgreSQL', 'Docker'. "
            "Use the official name — not abbreviations or alternate spellings."
        )
    )
    category: _CategoryLiteral = Field(
        description=(
            "Skill category. Must be exactly one of: "
            + ", ".join(CANONICAL_CATEGORIES)
        )
    )
    proficiency_level: str = Field(
        description=(
            "Candidate's proficiency level. "
            "Must be exactly one of: beginner, intermediate, advanced, expert. "
            "Infer from context (years of experience, seniority language, "
            "certifications). Default to 'intermediate' when unclear."
        )
    )


class _ExperienceOut(BaseModel):
    role: str = Field(description="Job title / role held")
    company: str = Field(description="Employer name")
    duration_months: int = Field(
        description="Duration in whole months (estimate if only years given)"
    )
    responsibilities: list[str] = Field(
        description="Key responsibilities or achievements, one sentence each"
    )


class _EducationOut(BaseModel):
    degree: str = Field(description="Degree or qualification name")
    institution: str = Field(description="University, college, or school name")
    graduation_year: int = Field(description="Year of graduation or expected graduation")


class _ParsedOut(BaseModel):
    skills: list[_SkillOut] = Field(
        description=(
            "Technical skills only — no soft skills. "
            "Maximum 20. Prioritize languages > frameworks > databases "
            "over tooling and methodology when truncating."
        )
    )
    experiences: list[_ExperienceOut] = Field(
        description="All work experience entries in reverse-chronological order"
    )
    education: list[_EducationOut] = Field(
        description="All education entries"
    )


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM = """\
You are an expert resume parser specializing in technical roles.
Extract structured information from the resume text provided by the user.

SKILLS EXTRACTION RULES:
- Extract ONLY concrete technical skills: programming languages, frameworks, \
databases, cloud platforms, DevOps tools, software architecture patterns, \
data science libraries, development tools, testing frameworks, and methodologies.
- DO NOT extract: soft skills (communication, teamwork, leadership, \
problem-solving, adaptability), generic personality traits (fast learner, \
detail-oriented), or vague competencies (project management, stakeholder \
communication).
- Classify each skill into EXACTLY ONE of these categories (choose the best fit):
    language     — programming/query languages (Python, Go, TypeScript, SQL, Rust, Java)
    framework    — application frameworks and libraries (Django, React, FastAPI, Spring, Next.js)
    database     — databases and data stores (PostgreSQL, Redis, MongoDB, Elasticsearch, MySQL)
    cloud        — cloud platforms and managed services (AWS, GCP, Azure)
    devops       — infrastructure, deployment, and ops tools (Docker, Kubernetes, CI/CD, Terraform, Linux, Nginx)
    architecture — design patterns and API paradigms (REST APIs, GraphQL, Microservices, Event-driven, gRPC)
    data-science — ML/data libraries and platforms (Pandas, TensorFlow, PyTorch, scikit-learn, NumPy, Spark)
    tooling      — developer tools and local environment (Git, VS Code, Webpack, Jira, Figma)
    testing      — testing frameworks and quality practices (pytest, Jest, Cypress, unit testing, TDD)
    methodology  — development processes (Agile, Scrum, Kanban, DevOps culture)
- Infer proficiency_level from context clues:
    expert       — "expert in", "deep expertise", lead/principal engineer, 5+ years with a skill
    advanced     — "proficient", "strong", senior engineer, 3-5 years with a skill
    intermediate — "experience with", mid-level engineer, 1-3 years, or unclear
    beginner     — "familiar with", "exposure to", "basic knowledge", < 1 year
  Default to "intermediate" when no contextual clue is available.
- Extract at most 20 skills total. If more are present, prioritize:
  languages > frameworks > databases > cloud > devops > architecture \
> data-science > tooling > testing > methodology.
- Normalize skill names to their canonical form: "PostgreSQL" not "Postgres", \
"TypeScript" not "TS", "Kubernetes" not "K8s", "JavaScript" not "JS".
- Remove duplicates (same skill mentioned under different names counts once).

EXPERIENCE RULES:
- Estimate duration_months from dates. Years-only → multiply by 12. No dates → 0.
- Keep responsibilities concise (max 3-5 bullet-point sentences per role).

GENERAL:
- Return empty lists for sections absent in the resume.
- Do not hallucinate — only extract information explicitly present in the text.
"""

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human", "{text}"),
])


# ---------------------------------------------------------------------------
# Parser implementation
# ---------------------------------------------------------------------------


class GeminiResumeParser(AIAnalysisPort):
    """
    Parses a raw resume text into structured skills, experiences, and education
    using Google Gemini via LangChain's structured output binding.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash-lite",
    ) -> None:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0,
        )
        self._chain = _PROMPT | llm.with_structured_output(_ParsedOut)

    def parse(self, text: str) -> ParsedResumeData:
        """
        Invoke Gemini with structured output binding and map the result to
        application-layer DTOs.

        Raises:
            Any LangChain / Google API exception on network failure, quota
            exhaustion, or invalid model output. The use case wraps these in
            AIAnalysisError.
        """
        result: _ParsedOut = self._chain.invoke({"text": text})

        # Deduplicate skills by (normalised name, normalised category) — Gemini
        # occasionally returns the same skill twice with minor casing differences.
        seen: set[tuple[str, str]] = set()
        unique_skills: list[_SkillOut] = []
        for s in result.skills:
            key = (s.name.strip().lower(), s.category.strip().lower())
            if key not in seen:
                seen.add(key)
                unique_skills.append(s)

        return ParsedResumeData(
            skills=[
                SkillDTO(
                    name=s.name,
                    category=s.category,
                    proficiency_level=s.proficiency_level,
                )
                for s in unique_skills
            ],
            experiences=[
                ExperienceDTO(
                    role=e.role,
                    company=e.company,
                    duration_months=e.duration_months,
                    responsibilities=list(e.responsibilities),
                )
                for e in result.experiences
            ],
            education=[
                EducationDTO(
                    degree=ed.degree,
                    institution=ed.institution,
                    graduation_year=ed.graduation_year,
                )
                for ed in result.education
            ],
        )
