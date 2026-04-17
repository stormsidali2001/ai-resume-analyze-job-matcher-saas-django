"""
application/resume/ports.py

Application-level port interfaces for external services related to resumes.
Implementations live in the infrastructure layer (Phase 3+).
The application layer defines *what* it needs; infrastructure provides *how*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from application.resume.dtos import ParsedResumeData


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
    LangChain-powered resume parsing port.
    Extracts skills, work experiences, and education from raw resume text.
    The rule-based ResumeAnalysisService is used as a fallback when no
    implementation is wired up.
    """

    @abstractmethod
    def parse(self, text: str) -> ParsedResumeData:
        """
        Use an AI model to extract structured resume data from raw text.

        Args:
            text: Raw resume text.

        Returns:
            ParsedResumeData with skills, experiences, and education.

        Raises:
            Exception: Any error from the underlying AI service (network,
                       quota, bad output). The use case wraps these in
                       AIAnalysisError.
        """
