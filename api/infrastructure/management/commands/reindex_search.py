"""
infrastructure/management/commands/reindex_search.py

Bulk-queue Elasticsearch indexing tasks for all published jobs and
analyzed resumes. Safe to re-run — tasks are idempotent upserts.

Usage:
    python manage.py reindex_search
    python manage.py reindex_search --jobs-only
    python manage.py reindex_search --resumes-only
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from infrastructure.search.client import get_es_client
from infrastructure.search.indices import (
    JOBS_INDEX,
    JOBS_MAPPING,
    RESUMES_INDEX,
    RESUMES_MAPPING,
)


def _ensure_indices(recreate: bool = False) -> None:
    """Create indices, optionally dropping and recreating them."""
    es = get_es_client()
    for index, mapping in ((JOBS_INDEX, JOBS_MAPPING), (RESUMES_INDEX, RESUMES_MAPPING)):
        exists = es.indices.exists(index=index)
        if exists and recreate:
            es.indices.delete(index=index)
            exists = False
        if not exists:
            es.indices.create(index=index, body=mapping)


class Command(BaseCommand):
    help = "Queue Celery tasks to (re)index all published jobs and analyzed resumes in Elasticsearch."

    def add_arguments(self, parser):
        parser.add_argument(
            "--jobs-only",
            action="store_true",
            help="Only reindex jobs.",
        )
        parser.add_argument(
            "--resumes-only",
            action="store_true",
            help="Only reindex resumes.",
        )
        parser.add_argument(
            "--recreate-indices",
            action="store_true",
            help="Drop and recreate indices before queuing tasks (needed after mapping changes).",
        )

    def handle(self, *args, **options):
        _ensure_indices(recreate=options["recreate_indices"])
        self.stdout.write("Elasticsearch indices ready.")

        jobs_only = options["jobs_only"]
        resumes_only = options["resumes_only"]

        if not resumes_only:
            self._reindex_jobs()

        if not jobs_only:
            self._reindex_resumes()

        self.stdout.write(self.style.SUCCESS("Reindex tasks queued."))

    def _reindex_jobs(self) -> None:
        from infrastructure.models.job import JobRecord
        from infrastructure.tasks.search_tasks import index_job_task

        job_ids = list(
            JobRecord.objects.filter(status="PUBLISHED").values_list("job_id", flat=True)
        )
        for job_id in job_ids:
            index_job_task.delay(str(job_id))

        self.stdout.write(f"  Queued {len(job_ids)} job indexing tasks.")

    def _reindex_resumes(self) -> None:
        from infrastructure.models.resume import ResumeRecord
        from infrastructure.tasks.search_tasks import index_resume_task

        resume_ids = list(
            ResumeRecord.objects.filter(analysis_status__in=["done", "idle"]).values_list(
                "resume_id", flat=True
            )
        )
        for resume_id in resume_ids:
            index_resume_task.delay(str(resume_id))

        self.stdout.write(f"  Queued {len(resume_ids)} resume indexing tasks.")
