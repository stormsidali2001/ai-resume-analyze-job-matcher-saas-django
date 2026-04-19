"""
interfaces/api/v1/job/views.py

JobViewSet — list/retrieve are public; write actions require recruiter role.
"""

from __future__ import annotations

from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from application.job.dtos import AddSkillToJobCommand, CreateJobCommand, SalaryRangeDTO
from interfaces.api.dependencies import get_job_use_cases
from interfaces.api.v1.job.serializers import (
    AddSkillToJobRequestSerializer,
    CreateJobRequestSerializer,
    JobDTOSerializer,
)

_PUBLISHED_JOBS_KEY = "published_jobs"
_PUBLISHED_JOBS_TTL = 5 * 60  # 5 minutes


@extend_schema_view(
    list=extend_schema(
        summary="List published jobs",
        description="Public endpoint. Returns all currently published job postings.",
        responses={200: JobDTOSerializer(many=True)},
        tags=["Jobs"],
    ),
    create=extend_schema(
        summary="Create a job posting",
        description="Create a new job in DRAFT status. Authentication required.",
        request=CreateJobRequestSerializer,
        responses={201: JobDTOSerializer},
        tags=["Jobs"],
    ),
    retrieve=extend_schema(
        summary="Get a job posting",
        description="Public endpoint. Returns a single job by ID.",
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        responses={200: JobDTOSerializer, 404: OpenApiResponse(description="Not found")},
        tags=["Jobs"],
    ),
)
class JobViewSet(ViewSet):
    """Job postings. List/retrieve are public; all write actions require auth."""

    # Helps drf-spectacular resolve the default response schema for unannotated actions
    serializer_class = JobDTOSerializer
    lookup_value_regex = r"[0-9a-f-]{36}"

    def get_permissions(self):
        public_actions = ("list", "retrieve")
        if self.action in public_actions:
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request: Request) -> Response:
        cached = cache.get(_PUBLISHED_JOBS_KEY)
        if cached is not None:
            return Response(cached)

        use_cases = get_job_use_cases()
        dtos = use_cases["list_published"].execute()
        data = JobDTOSerializer(dtos, many=True).data
        cache.set(_PUBLISHED_JOBS_KEY, data, timeout=_PUBLISHED_JOBS_TTL)
        return Response(data)

    def create(self, request: Request) -> Response:
        ser = CreateJobRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        salary_range = None
        if data.get("salary_range"):
            sr = data["salary_range"]
            salary_range = SalaryRangeDTO(
                min_salary=sr["min_salary"],
                max_salary=sr["max_salary"],
                currency=sr.get("currency", "USD"),
            )

        cmd = CreateJobCommand(
            recruiter_id=str(request.user.id),
            title=data["title"],
            company=data["company"],
            description=data["description"],
            city=data["city"],
            country=data["country"],
            remote=data.get("remote", False),
            employment_type=data["employment_type"],
            required_experience_months=data.get("required_experience_months", 0),
            salary_range=salary_range,
        )
        use_cases = get_job_use_cases()
        dto = use_cases["create"].execute(cmd)
        return Response(JobDTOSerializer(dto).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, pk: str) -> Response:
        use_cases = get_job_use_cases()
        dto = use_cases["get"].execute(pk)
        return Response(JobDTOSerializer(dto).data)

    @extend_schema(
        summary="List my jobs",
        description="Returns all jobs (any status) created by the authenticated recruiter.",
        responses={200: JobDTOSerializer(many=True)},
        tags=["Jobs"],
    )
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request: Request) -> Response:
        use_cases = get_job_use_cases()
        dtos = use_cases["list_mine"].execute(recruiter_id=str(request.user.id))
        return Response(JobDTOSerializer(dtos, many=True).data)

    @extend_schema(
        summary="Add required skill",
        description="Attach a required skill to the job. Authentication required.",
        request=AddSkillToJobRequestSerializer,
        responses={201: JobDTOSerializer},
        tags=["Jobs"],
    )
    @action(detail=True, methods=["post"], url_path="skills")
    def add_skill(self, request: Request, pk: str) -> Response:
        ser = AddSkillToJobRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        cmd = AddSkillToJobCommand(
            job_id=pk,
            recruiter_id=str(request.user.id),
            **ser.validated_data,
        )
        use_cases = get_job_use_cases()
        dto = use_cases["add_skill"].execute(cmd)
        return Response(JobDTOSerializer(dto).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Publish job",
        description="Transition the job from DRAFT to PUBLISHED. Requires at least one required skill.",
        responses={200: JobDTOSerializer, 403: OpenApiResponse(description="Not the owner"), 422: OpenApiResponse(description="No required skills")},
        tags=["Jobs"],
    )
    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request: Request, pk: str) -> Response:
        use_cases = get_job_use_cases()
        dto = use_cases["publish"].execute(pk, str(request.user.id))
        cache.delete(_PUBLISHED_JOBS_KEY)
        return Response(JobDTOSerializer(dto).data)

    @extend_schema(
        summary="Close job",
        description="Transition the job from PUBLISHED to CLOSED. No further applications accepted.",
        responses={200: JobDTOSerializer, 403: OpenApiResponse(description="Not the owner")},
        tags=["Jobs"],
    )
    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request: Request, pk: str) -> Response:
        use_cases = get_job_use_cases()
        dto = use_cases["close"].execute(pk, str(request.user.id))
        cache.delete(_PUBLISHED_JOBS_KEY)
        return Response(JobDTOSerializer(dto).data)
