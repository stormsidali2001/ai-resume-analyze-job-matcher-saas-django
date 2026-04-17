"""
infrastructure/files/pdf_parser.py

pdfplumber-based implementation of FileParserPort.
Extracts plain text from PDF bytes in memory — no disk writes.
"""

from __future__ import annotations

import io

import pdfplumber

from application.resume.ports import FileParserPort


class PdfFileParser(FileParserPort):
    """Extracts plain text from PDF files using pdfplumber."""

    def parse(self, content: bytes, mime_type: str) -> str:
        if mime_type not in ("application/pdf", "application/octet-stream"):
            raise ValueError(f"Unsupported file type: {mime_type}. Only PDF files are accepted.")

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]

        text = "\n".join(pages).strip()
        if not text:
            raise ValueError(
                "Could not extract text from this PDF. "
                "Scanned/image-only PDFs are not supported."
            )
        return text
