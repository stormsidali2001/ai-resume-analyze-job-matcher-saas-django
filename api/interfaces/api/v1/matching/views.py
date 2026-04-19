"""
interfaces/api/v1/matching/views.py

MatchView — POST /api/v1/match/ to score a resume against a job posting.
BatchMatchView — POST /api/v1/match/batch/ to score one resume against many jobs concurrently.
"""

from __future__ import annotations

from django.core.cache import cache
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from application.matching.dtos import BatchMatchCommand, MatchRequestCommand
from interfaces.api.dependencies import get_match_use_case
from interfaces.api.v1.matching.serializers import (
    BatchMatchRequestSerializer,
    BatchMatchResultSerializer,
    MatchRequestSerializer,
    MatchResultDTOSerializer,
)

_MATCH_CACHE_TTL = 60 * 60  # 1 hour — same inputs always yield the same score


class MatchView(APIView):
    """Match a candidate's resume against a job posting. Results are cached for 1 hour."""

    @extend_schema(
        summary="Match resume to job",
        description=(
            "Score a resume against a job posting using a weighted algorithm:\n\n"
            "- **60 pts** — skill overlap\n"
            "- **30 pts** — experience match\n"
            "- **10 pts** — base / contact completeness\n\n"
            "Returns the score (0–100), a label (poor / weak / acceptable / strong), "
            "identified gaps, and improvement suggestions.\n\n"
            "Results are cached in Redis for 1 hour. The cache is invalidated automatically "
            "when a Celery worker completes an AI re-analysis of the resume."
        ),
        request=MatchRequestSerializer,
        responses={
            200: MatchResultDTOSerializer,
            403: OpenApiResponse(description="Resume does not belong to the authenticated user"),
            404: OpenApiResponse(description="Resume or job not found"),
        },
        tags=["Matching"],
    )
    def post(self, request: Request) -> Response:
        ser = MatchRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        resume_id = ser.validated_data["resume_id"]
        job_id = ser.validated_data["job_id"]
        candidate_id = str(request.user.id)

        cache_key = f"match:{resume_id}:{job_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        cmd = MatchRequestCommand(
            resume_id=resume_id,
            candidate_id=candidate_id,
            job_id=job_id,
        )
        use_case = get_match_use_case()
        dto = use_case.execute(cmd)
        data = MatchResultDTOSerializer(dto).data
        cache.set(cache_key, data, timeout=_MATCH_CACHE_TTL)
        return Response(data, status=status.HTTP_200_OK)


class BatchMatchView(APIView):
    """Score one resume against up to 10 jobs concurrently using asyncio."""

    @extend_schema(
        summary="Batch match resume to jobs",
        description=(
            "Score a single resume against up to **10** job postings in one request.\n\n"
            "Job fetches are executed concurrently with `asyncio.gather` + `sync_to_async`, "
            "making this significantly faster than calling the single-match endpoint in a loop.\n\n"
            "Results are returned sorted by score descending. Jobs that cannot be found are "
            "silently omitted from the response."
        ),
        request=BatchMatchRequestSerializer,
        responses={
            200: BatchMatchResultSerializer,
            403: OpenApiResponse(description="Resume does not belong to the authenticated user"),
            404: OpenApiResponse(description="Resume not found"),
        },
        tags=["Matching"],
    )
    async def post(self, request: Request) -> Response:
        ser = BatchMatchRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        cmd = BatchMatchCommand(
            resume_id=ser.validated_data["resume_id"],
            candidate_id=str(request.user.id),
            job_ids=ser.validated_data["job_ids"],
        )
        use_case = get_match_use_case()
        dtos = await use_case.execute_batch_async(cmd)
        data = {"results": MatchResultDTOSerializer(dtos, many=True).data}
        return Response(data, status=status.HTTP_200_OK)
