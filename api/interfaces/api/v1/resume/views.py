"""
interfaces/api/v1/resume/views.py

ResumeViewSet — each action delegates to the corresponding application use case.
"""

from __future__ import annotations

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from application.resume.dtos import (
    AddSkillCommand,
    AnalyzeResumeCommand,
    CreateResumeCommand,
    UpdateResumeTextCommand,
)
from infrastructure.models.resume import ResumeRecord
from infrastructure.tasks.resume_tasks import analyze_resume_task
from interfaces.api.dependencies import get_file_parser, get_resume_use_cases, get_resume_use_cases_no_ai
from interfaces.api.v1.resume.serializers import (
    AddSkillRequestSerializer,
    AnalyzeResumeRequestSerializer,
    CreateResumeRequestSerializer,
    ResumeDTOSerializer,
    ResumeFileUploadSerializer,
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
        description="Upload raw resume text and contact info. Returns a DRAFT resume immediately (202). AI analysis runs in the background — poll the resume until analysis_status is 'done'.",
        request=CreateResumeRequestSerializer,
        responses={202: ResumeDTOSerializer},
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
        # Save immediately with keyword-based extraction (no AI wait)
        use_cases = get_resume_use_cases_no_ai()
        dto = use_cases["create"].execute(cmd)
        # Queue full AI analysis in the background
        analyze_resume_task.delay(dto.resume_id, str(request.user.id))
        return Response(ResumeDTOSerializer(dto).data, status=status.HTTP_202_ACCEPTED)

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
        description="Queue a background AI analysis of the resume. Returns 202 immediately. Poll the resume until analysis_status is 'done'.",
        responses={202: OpenApiResponse(description="Analysis queued")},
        tags=["Resumes"],
    )
    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request: Request, pk: str) -> Response:
        # Mark as pending immediately so the client can start polling
        ResumeRecord.objects.filter(resume_id=pk).update(
            analysis_status="pending", updated_at=timezone.now()
        )
        analyze_resume_task.delay(pk, str(request.user.id))
        return Response({"resume_id": pk, "analysis_status": "pending"}, status=status.HTTP_202_ACCEPTED)

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

    @extend_schema(
        summary="Upload resume PDF",
        description="Upload a PDF file and contact info. Text is extracted and saved immediately (202). AI analysis runs in the background — poll the resume until analysis_status is 'done'.",
        request=ResumeFileUploadSerializer,
        responses={202: ResumeDTOSerializer, 400: OpenApiResponse(description="Invalid file or unsupported type")},
        tags=["Resumes"],
    )
    @action(detail=False, methods=["post"], url_path="upload", parser_classes=[MultiPartParser])
    def upload(self, request: Request) -> Response:
        ser = ResumeFileUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        uploaded_file = ser.validated_data["file"]
        file_parser = get_file_parser()

        try:
            raw_text = file_parser.parse(
                uploaded_file.read(),
                uploaded_file.content_type or "application/pdf",
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        cmd = CreateResumeCommand(
            candidate_id=str(request.user.id),
            raw_text=raw_text,
            email=ser.validated_data["email"],
            phone=ser.validated_data["phone"],
            location=ser.validated_data["location"],
        )
        # Save immediately with keyword-based extraction (no AI wait)
        use_cases = get_resume_use_cases_no_ai()
        dto = use_cases["create"].execute(cmd)
        # Queue full AI analysis in the background
        analyze_resume_task.delay(dto.resume_id, str(request.user.id))
        return Response(ResumeDTOSerializer(dto).data, status=status.HTTP_202_ACCEPTED)
