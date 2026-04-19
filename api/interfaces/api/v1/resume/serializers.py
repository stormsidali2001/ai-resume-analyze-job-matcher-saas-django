"""
interfaces/api/v1/resume/serializers.py

Request and response serializers for the resume resource.
"""

from rest_framework import serializers


# ── Response serializers ───────────────────────────────────────────────────

class ContactInfoSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField()
    location = serializers.CharField()


class SkillSerializer(serializers.Serializer):
    name = serializers.CharField()
    category = serializers.CharField()
    proficiency_level = serializers.CharField()


class ExperienceSerializer(serializers.Serializer):
    role = serializers.CharField()
    company = serializers.CharField()
    duration_months = serializers.IntegerField()
    responsibilities = serializers.ListField(child=serializers.CharField())


class EducationSerializer(serializers.Serializer):
    degree = serializers.CharField()
    institution = serializers.CharField()
    graduation_year = serializers.IntegerField()


class ResumeDTOSerializer(serializers.Serializer):
    resume_id = serializers.CharField()
    candidate_id = serializers.CharField()
    status = serializers.CharField()
    analysis_status = serializers.CharField()
    raw_text_preview = serializers.CharField()
    contact_info = ContactInfoSerializer()
    skills = SkillSerializer(many=True)
    experiences = ExperienceSerializer(many=True)
    education = EducationSerializer(many=True)
    total_experience_months = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


# ── Request serializers ────────────────────────────────────────────────────

class CreateResumeRequestSerializer(serializers.Serializer):
    raw_text = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    location = serializers.CharField()


class UpdateResumeTextRequestSerializer(serializers.Serializer):
    new_raw_text = serializers.CharField()


class AnalyzeResumeRequestSerializer(serializers.Serializer):
    known_skills = serializers.ListField(child=serializers.CharField(), default=list)


class AddSkillRequestSerializer(serializers.Serializer):
    PROFICIENCY_CHOICES = ["beginner", "intermediate", "advanced", "expert"]
    name = serializers.CharField()
    category = serializers.CharField()
    proficiency_level = serializers.ChoiceField(choices=PROFICIENCY_CHOICES)


class ResumeFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    location = serializers.CharField()
