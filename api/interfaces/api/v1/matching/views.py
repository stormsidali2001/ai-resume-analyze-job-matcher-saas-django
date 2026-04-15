"""
interfaces/api/v1/matching/views.py

MatchView — POST /api/v1/match/ to score a resume against a job posting.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from application.matching.dtos import MatchRequestCommand
from interfaces.api.dependencies import get_match_use_case
from interfaces.api.v1.matching.serializers import MatchRequestSerializer, MatchResultDTOSerializer


class MatchView(APIView):
    """Match a candidate's resume against a job posting."""

    @extend_schema(
        summary="Match resume to job",
        description=(
            "Score a resume against a job posting using a weighted algorithm:\n\n"
            "- **60 pts** — skill overlap\n"
            "- **30 pts** — experience match\n"
            "- **10 pts** — base / contact completeness\n\n"
            "Returns the score (0–100), a label (poor / weak / acceptable / strong), "
            "identified gaps, and improvement suggestions."
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

        cmd = MatchRequestCommand(
            resume_id=ser.validated_data["resume_id"],
            candidate_id=str(request.user.id),
            job_id=ser.validated_data["job_id"],
        )
        use_case = get_match_use_case()
        dto = use_case.execute(cmd)
        return Response(MatchResultDTOSerializer(dto).data, status=status.HTTP_200_OK)
