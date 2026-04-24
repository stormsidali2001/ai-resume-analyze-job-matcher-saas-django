"""
infrastructure/search/retriever.py

Hybrid BM25 + kNN search for jobs and resumes.

Both functions return a list of raw ES source dicts — the caller
(ChatConsumer) is responsible for formatting them for display.
"""

from __future__ import annotations

from infrastructure.search.client import get_es_client
from infrastructure.search.embeddings import embed_query
from infrastructure.search.indices import JOBS_INDEX, RESUMES_INDEX


def search_jobs(query: str, top_k: int = 5) -> list[dict]:
    """Hybrid search over the jobs index for a candidate query."""
    vec = embed_query(query)
    resp = get_es_client().search(
        index=JOBS_INDEX,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "company^2", "description", "skills^2"],
                }
            },
            "knn": {
                "field": "embedding",
                "query_vector": vec,
                "k": top_k,
                "num_candidates": top_k * 10,
                "boost": 0.5,
            },
            "size": top_k,
        },
    )
    return [h["_source"] for h in resp["hits"]["hits"]]


def search_resumes(query: str, top_k: int = 5) -> list[dict]:
    """Hybrid search over the resumes index for a recruiter query."""
    vec = embed_query(query)
    resp = get_es_client().search(
        index=RESUMES_INDEX,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["raw_text", "skills^2", "location"],
                }
            },
            "knn": {
                "field": "embedding",
                "query_vector": vec,
                "k": top_k,
                "num_candidates": top_k * 10,
                "boost": 0.5,
            },
            "size": top_k,
        },
    )
    return [h["_source"] for h in resp["hits"]["hits"]]
