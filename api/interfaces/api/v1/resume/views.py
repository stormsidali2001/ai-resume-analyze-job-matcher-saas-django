"""
interfaces/api/v1/resume/views.py

ResumeViewSet — each action delegates to the corresponding application use case.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from application.resume.dtos import (
    AddSkillCommand,
    AnalyzeResumeCommand,
    CreateResumeCommand,
    UpdateResumeTextCommand,
)
from interfaces.api.dependencies import get_resume_use_cases
from interfaces.api.v1.resume.serializers import (
    AddSkillRequestSerializer,
    AnalyzeResumeRequestSerializer,
    CreateResumeRequestSerializer,
    ResumeDTOSerializer,
    UpdateResumeTextRequestSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List your resumes",
        description="Returns all resumes belonging to the authenticated candidate.",
        responses={200: ResumeDTOSerializer(many=True)},
        tags=["Resumes"],
    ),
    create=extend_schema(
        summary="Create a resume",
        description="Upload raw resume text and contact info. Returns a DRAFT resume.",
        request=CreateResumeRequestSerializer,
        responses={201: ResumeDTOSerializer},
        tags=["Resumes"],
    ),
    retrieve=extend_schema(
        summary="Get a resume",
        description="Fetch a single resume. Only the owning candidate may access it.",
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        responses={200: ResumeDTOSerializer, 403: OpenApiResponse(description="Not the owner"), 404: OpenApiResponse(description="Not found")},
        tags=["Resumes"],
    ),
    partial_update=extend_schema(
        summary="Update resume text",
        description="Replace the raw text of a resume. Resets extracted skills.",
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        request=UpdateResumeTextRequestSerializer,
        responses={200: ResumeDTOSerializer},
        tags=["Resumes"],
    ),
)
class ResumeViewSet(ViewSet):
    """Candidate-scoped resume operations. All actions require authentication."""

    serializer_class = ResumeDTOSerializer
    lookup_value_regex = r"[0-9a-f-]{36}"

    def list(self, request: Request) -> Response:
        candidate_id = str(request.user.id)
        use_cases = get_resume_use_cases()
        dtos = use_cases["list"].execute(candidate_id)
        return Response(ResumeDTOSerializer(dtos, many=True).data)

    def create(self, request: Request) -> Response:
        ser = CreateResumeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        cmd = CreateResumeCommand(
            candidate_id=str(request.user.id),
            **ser.validated_data,
        )
        use_cases = get_resume_use_cases()
        dto = use_cases["create"].execute(cmd)
        return Response(ResumeDTOSerializer(dto).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, pk: str) -> Response:
        use_cases = get_resume_use_cases()
        dto = use_cases["get"].execute(pk, str(request.user.id))
        return Response(ResumeDTOSerializer(dto).data)

    def partial_update(self, request: Request, pk: str) -> Response:
        ser = UpdateResumeTextRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        cmd = UpdateResumeTextCommand(
            resume_id=pk,
            candidate_id=str(request.user.id),
            new_raw_text=ser.validated_data["new_raw_text"],
        )
        use_cases = get_resume_use_cases()
        dto = use_cases["update_text"].execute(cmd)
        return Response(ResumeDTOSerializer(dto).data)

    @extend_schema(
        summary="Analyze resume",
        description="Scan the resume text for known skills and attach them to the resume.",
        request=AnalyzeResumeRequestSerializer,
        responses={200: ResumeDTOSerializer},
        tags=["Resumes"],
    )
    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request: Request, pk: str) -> Response:
        ser = AnalyzeResumeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        cmd = AnalyzeResumeCommand(
            resume_id=pk,
            candidate_id=str(request.user.id),
            known_skills=ser.validated_data.get("known_skills", []),
        )
        use_cases = get_resume_use_cases()
        dto = use_cases["analyze"].execute(cmd)
        return Response(ResumeDTOSerializer(dto).data)

    @extend_schema(
        summary="Add skill",
        description="Manually add a skill to the resume.",
        request=AddSkillRequestSerializer,
        responses={201: ResumeDTOSerializer},
        tags=["Resumes"],
    )
    @action(detail=True, methods=["post"], url_path="skills")
    def add_skill(self, request: Request, pk: str) -> Response:
        ser = AddSkillRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        cmd = AddSkillCommand(
            resume_id=pk,
            candidate_id=str(request.user.id),
            **ser.validated_data,
        )
        use_cases = get_resume_use_cases()
        dto = use_cases["add_skill"].execute(cmd)
        return Response(ResumeDTOSerializer(dto).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Archive resume",
        description="Move the resume to ARCHIVED status. This action cannot be undone.",
        responses={204: OpenApiResponse(description="Archived — no content")},
        tags=["Resumes"],
    )
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request: Request, pk: str) -> Response:
        use_cases = get_resume_use_cases()
        use_cases["archive"].execute(pk, str(request.user.id))
        return Response(status=status.HTTP_204_NO_CONTENT)
