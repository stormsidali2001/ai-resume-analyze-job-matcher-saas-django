"""
application/resume/ports.py

Application-level port interfaces for external services related to resumes.
Implementations live in the infrastructure layer (Phase 3+).
The application layer defines *what* it needs; infrastructure provides *how*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from application.resume.dtos import SkillDTO


class FileParserPort(ABC):
    """
    Parses raw file bytes (PDF, DOCX, etc.) into plain text.
    Used by the file upload flow before resume creation.
    """

    @abstractmethod
    def parse(self, content: bytes, mime_type: str) -> str:
        """
        Extract plain text from a binary file.

        Args:
            content: Raw file bytes.
            mime_type: MIME type string (e.g. 'application/pdf').

        Returns:
            Extracted plain text.

        Raises:
            ValueError: If the mime_type is unsupported.
        """


class AIAnalysisPort(ABC):
    """
    LangChain-powered skill extraction port (Phase 3+).
    The rule-based ResumeAnalysisService is used until this is wired up.
    """

    @abstractmethod
    def extract_skills(self, text: str) -> list[SkillDTO]:
        """
        Use an AI model to extract structured skills from resume text.

        Args:
            text: Raw resume text.

        Returns:
            List of SkillDTOs identified by the model.
        """
