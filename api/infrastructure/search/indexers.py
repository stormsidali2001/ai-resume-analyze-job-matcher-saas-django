"""
infrastructure/search/indexers.py

Index and delete helpers for jobs and resumes.
Called by Celery tasks — not the application layer directly.
"""

from __future__ import annotations

from infrastructure.search.client import get_es_client
from infrastructure.search.embeddings import embed_document
from infrastructure.search.indices import JOBS_INDEX, RESUMES_INDEX


def index_job(job_record) -> None:
    """Embed and upsert a job into the jobs index."""
    text = f"{job_record.title} at {job_record.company}. {job_record.description}"
    embedding = embed_document(text)
    es = get_es_client()
    es.index(
        index=JOBS_INDEX,
        id=str(job_record.job_id),
        document={
            "job_id": str(job_record.job_id),
            "title": job_record.title,
            "company": job_record.company,
            "description": job_record.description,
            "skills": [s.name for s in job_record.required_skills.all()],
            "location": f"{job_record.location_city}, {job_record.location_country}",
            "employment_type": job_record.employment_type,
            "required_experience_months": job_record.required_experience_months,
            "embedding": embedding,
        },
    )


def delete_job(job_id: str) -> None:
    """Remove a job document from the jobs index."""
    es = get_es_client()
    try:
        es.delete(index=JOBS_INDEX, id=job_id)
    except Exception:
        pass  # Already absent — not an error


def index_resume(resume_record) -> None:
    """Embed and upsert a resume into the resumes index."""
    skills = [s.name for s in resume_record.skills.all()]
    text = resume_record.raw_text
    embedding = embed_document(text)
    es = get_es_client()
    es.index(
        index=RESUMES_INDEX,
        id=str(resume_record.resume_id),
        document={
            "resume_id": str(resume_record.resume_id),
            "candidate_id": str(resume_record.candidate_id),
            "raw_text": resume_record.raw_text,
            "skills": skills,
            "location": resume_record.contact_location,
            "total_experience_months": sum(
                e.duration_months for e in resume_record.experiences.all()
            ),
            "embedding": embedding,
        },
    )
