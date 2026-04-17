"""
tests/infrastructure/test_gemini_resume_parser.py

Unit tests for GeminiResumeParser. The LangChain chain is mocked so no
real API calls are made. Tests verify that the parser correctly maps the
model output to application-layer DTOs.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from application.resume.dtos import ParsedResumeData


@pytest.fixture()
def parser():
    """Return a GeminiResumeParser with the LangChain chain mocked out."""
    # Patch at import time so ChatGoogleGenerativeAI is never instantiated
    with patch("infrastructure.ai.gemini_resume_parser.ChatGoogleGenerativeAI"):
        from infrastructure.ai.gemini_resume_parser import GeminiResumeParser

        instance = GeminiResumeParser(api_key="fake-key")
        yield instance


def _make_chain_result(skills=None, experiences=None, education=None):
    """Build a mock _ParsedOut object that the chain would normally return."""
    result = MagicMock()
    result.skills = skills or []
    result.experiences = experiences or []
    result.education = education or []
    return result


class TestGeminiResumeParserParse:
    def test_returns_parsed_resume_data(self, parser):
        skill = MagicMock(name="Python", category="programming", proficiency_level="advanced")
        skill.name = "Python"
        skill.category = "programming"
        skill.proficiency_level = "advanced"

        exp = MagicMock()
        exp.role = "Backend Engineer"
        exp.company = "Acme Corp"
        exp.duration_months = 24
        exp.responsibilities = ["Built APIs", "Led a team of 3"]

        edu = MagicMock()
        edu.degree = "BSc Computer Science"
        edu.institution = "MIT"
        edu.graduation_year = 2019

        parser._chain = MagicMock()
        parser._chain.invoke.return_value = _make_chain_result(
            skills=[skill], experiences=[exp], education=[edu]
        )

        result = parser.parse("Some resume text")

        assert isinstance(result, ParsedResumeData)
        assert len(result.skills) == 1
        assert result.skills[0].name == "Python"
        assert result.skills[0].category == "programming"
        assert result.skills[0].proficiency_level == "advanced"

        assert len(result.experiences) == 1
        assert result.experiences[0].role == "Backend Engineer"
        assert result.experiences[0].company == "Acme Corp"
        assert result.experiences[0].duration_months == 24
        assert result.experiences[0].responsibilities == ["Built APIs", "Led a team of 3"]

        assert len(result.education) == 1
        assert result.education[0].degree == "BSc Computer Science"
        assert result.education[0].institution == "MIT"
        assert result.education[0].graduation_year == 2019

    def test_empty_sections_return_empty_lists(self, parser):
        parser._chain = MagicMock()
        parser._chain.invoke.return_value = _make_chain_result()

        result = parser.parse("Minimal resume text")

        assert result.skills == []
        assert result.experiences == []
        assert result.education == []

    def test_passes_text_to_chain(self, parser):
        parser._chain = MagicMock()
        parser._chain.invoke.return_value = _make_chain_result()

        parser.parse("My awesome resume content")

        parser._chain.invoke.assert_called_once_with({"text": "My awesome resume content"})

    def test_propagates_chain_exception(self, parser):
        parser._chain = MagicMock()
        parser._chain.invoke.side_effect = RuntimeError("API quota exceeded")

        with pytest.raises(RuntimeError, match="API quota exceeded"):
            parser.parse("Some resume text")

    def test_multiple_skills_mapped_correctly(self, parser):
        skills_data = [
            ("Python", "programming", "expert"),
            ("Docker", "devops", "intermediate"),
            ("PostgreSQL", "databases", "advanced"),
        ]
        mock_skills = []
        for name, category, level in skills_data:
            s = MagicMock()
            s.name = name
            s.category = category
            s.proficiency_level = level
            mock_skills.append(s)

        parser._chain = MagicMock()
        parser._chain.invoke.return_value = _make_chain_result(skills=mock_skills)

        result = parser.parse("text")

        assert len(result.skills) == 3
        names = [s.name for s in result.skills]
        assert "Python" in names
        assert "Docker" in names
        assert "PostgreSQL" in names
