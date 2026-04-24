"""
infrastructure/search/embeddings.py

Thin wrappers around the Gemini text-embedding-004 API using google.genai.

Two task types are used:
- RETRIEVAL_DOCUMENT: for indexing content (jobs / resumes)
- RETRIEVAL_QUERY:    for embedding the user's search query at query time
"""

from __future__ import annotations

import google.genai as genai
from google.genai import types


def _get_client() -> genai.Client:
    from django.conf import settings
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def embed_document(text: str) -> list[float]:
    """Embed a document for indexing (task_type=RETRIEVAL_DOCUMENT)."""
    client = _get_client()
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return result.embeddings[0].values


def embed_query(text: str) -> list[float]:
    """Embed a user query for search (task_type=RETRIEVAL_QUERY)."""
    client = _get_client()
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return result.embeddings[0].values
