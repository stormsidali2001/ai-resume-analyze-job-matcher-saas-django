"""
infrastructure/tasks/search_tasks.py

Celery tasks for indexing and removing jobs/resumes from Elasticsearch.
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.index_job")
def index_job_task(self, job_id: str) -> None:
    """Embed and index a job into Elasticsearch."""
    try:
        from infrastructure.models.job import JobRecord
        from infrastructure.search.indexers import index_job

        job = JobRecord.objects.prefetch_related("required_skills").get(job_id=job_id)
        index_job(job)
        logger.info("index_job_task completed: job_id=%s", job_id)
    except Exception as exc:
        logger.exception("index_job_task failed: job_id=%s error=%s", job_id, exc)
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.delete_job_from_index")
def delete_job_from_index_task(self, job_id: str) -> None:
    """Remove a job document from the Elasticsearch index."""
    try:
        from infrastructure.search.indexers import delete_job

        delete_job(job_id)
        logger.info("delete_job_from_index_task completed: job_id=%s", job_id)
    except Exception as exc:
        logger.exception("delete_job_from_index_task failed: job_id=%s error=%s", job_id, exc)
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.index_resume")
def index_resume_task(self, resume_id: str) -> None:
    """Embed and index a resume into Elasticsearch."""
    try:
        from infrastructure.models.resume import ResumeRecord
        from infrastructure.search.indexers import index_resume

        resume = ResumeRecord.objects.prefetch_related("skills", "experiences").get(
            resume_id=resume_id
        )
        index_resume(resume)
        logger.info("index_resume_task completed: resume_id=%s", resume_id)
    except Exception as exc:
        logger.exception("index_resume_task failed: resume_id=%s error=%s", resume_id, exc)
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))
