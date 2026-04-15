"""
interfaces/api/v1/job/serializers.py

Request and response serializers for the job resource.
"""

from rest_framework import serializers


# ── Response serializers ───────────────────────────────────────────────────

class LocationSerializer(serializers.Serializer):
    city = serializers.CharField()
    country = serializers.CharField()
    remote = serializers.BooleanField()


class SalaryRangeSerializer(serializers.Serializer):
    min_salary = serializers.IntegerField()
    max_salary = serializers.IntegerField()
    currency = serializers.CharField()


class JobSkillSerializer(serializers.Serializer):
    name = serializers.CharField()
    category = serializers.CharField()
    proficiency_level = serializers.CharField()


class JobDTOSerializer(serializers.Serializer):
    job_id = serializers.CharField()
    recruiter_id = serializers.CharField()
    title = serializers.CharField()
    company = serializers.CharField()
    description_preview = serializers.CharField()
    required_skills = JobSkillSerializer(many=True)
    required_experience_months = serializers.IntegerField()
    location = LocationSerializer()
    employment_type = serializers.CharField()
    salary_range = SalaryRangeSerializer(allow_null=True)
    status = serializers.CharField()
    created_at = serializers.DateTimeField()


# ── Request serializers ────────────────────────────────────────────────────

EMPLOYMENT_TYPE_CHOICES = ["full_time", "part_time", "contract", "freelance", "internship"]
PROFICIENCY_CHOICES = ["beginner", "intermediate", "advanced", "expert"]


class SalaryRangeRequestSerializer(serializers.Serializer):
    min_salary = serializers.IntegerField(min_value=0)
    max_salary = serializers.IntegerField(min_value=0)
    currency = serializers.CharField(default="USD")


class CreateJobRequestSerializer(serializers.Serializer):
    title = serializers.CharField()
    company = serializers.CharField()
    description = serializers.CharField()
    city = serializers.CharField()
    country = serializers.CharField()
    remote = serializers.BooleanField(default=False)
    employment_type = serializers.ChoiceField(choices=EMPLOYMENT_TYPE_CHOICES)
    required_experience_months = serializers.IntegerField(min_value=0, default=0)
    salary_range = SalaryRangeRequestSerializer(required=False, allow_null=True)


class AddSkillToJobRequestSerializer(serializers.Serializer):
    name = serializers.CharField()
    category = serializers.CharField()
    proficiency_level = serializers.ChoiceField(choices=PROFICIENCY_CHOICES)
