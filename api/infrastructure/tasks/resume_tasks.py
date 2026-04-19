"""
infrastructure/tasks/resume_tasks.py

Celery tasks for background resume analysis.

The view creates the resume immediately (with fast keyword extraction as a stub),
then calls analyze_resume_task.delay() to run the full Gemini AI parse in the
background.

analysis_status lifecycle:
  pending → processing → done
                       ↘ failed  (retries up to 3× with exponential back-off)

Each transition is:
  1. Written directly to the DB (bypasses the aggregate stack for speed)
  2. Broadcast to the "resume_{id}" WebSocket channel group via Django Channels,
     so any connected browser tabs receive the update in real time.
"""

from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from infrastructure.models.resume import ResumeRecord

logger = logging.getLogger(__name__)


def _set_analysis_status(resume_id: str, new_status: str) -> None:
    """Direct model update — intentionally bypasses the full aggregate/repo stack."""
    ResumeRecord.objects.filter(resume_id=resume_id).update(
        analysis_status=new_status,
        updated_at=timezone.now(),
    )


def _broadcast_status(resume_id: str, new_status: str) -> None:
    """
    Push a status update to any WebSocket clients watching this resume.

    Uses Django Channels' channel layer (Redis DB 2). Errors are swallowed
    intentionally — a broadcast failure must never break the Celery task.
    """
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            f"resume_{resume_id}",
            {
                "type": "resume.status.update",
                "analysis_status": new_status,
                "resume_id": resume_id,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("_broadcast_status failed for %s: %s", resume_id, exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,   # seconds between retries (doubles on each attempt)
    name="tasks.analyze_resume",
)
def analyze_resume_task(self, resume_id: str, candidate_id: str) -> dict:
    """
    Run Gemini AI analysis on an existing resume and update its skills,
    experiences, and education in the database.

    Retries up to 3 times with exponential back-off if the AI call fails.
    Updates analysis_status at each stage so the frontend can poll for progress.
    """
    logger.info("analyze_resume_task started: resume_id=%s attempt=%s", resume_id, self.request.retries)

    try:
        _set_analysis_status(resume_id, "processing")
        _broadcast_status(resume_id, "processing")

        # Import here to avoid circular imports at module load time
        from application.resume.dtos import AnalyzeResumeCommand
        from interfaces.api.dependencies import get_resume_use_cases

        cmd = AnalyzeResumeCommand(
            resume_id=resume_id,
            candidate_id=candidate_id,
            known_skills=[],
        )
        get_resume_use_cases()["analyze"].execute(cmd)

        _set_analysis_status(resume_id, "done")
        _broadcast_status(resume_id, "done")

        # Invalidate any cached match results for this resume so re-analysis
        # is reflected immediately on the next match request.
        try:
            from django.core.cache import cache
            cache.delete_pattern(f"resumeai:match:{resume_id}:*")
        except Exception:
            pass  # cache miss or pattern-delete unsupported — not fatal

        logger.info("analyze_resume_task completed: resume_id=%s", resume_id)
        return {"resume_id": resume_id, "status": "done"}

    except Exception as exc:
        logger.exception("analyze_resume_task failed: resume_id=%s error=%s", resume_id, exc)
        _set_analysis_status(resume_id, "failed")
        _broadcast_status(resume_id, "failed")
        # Retry with exponential back-off; re-raise on final attempt
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))
