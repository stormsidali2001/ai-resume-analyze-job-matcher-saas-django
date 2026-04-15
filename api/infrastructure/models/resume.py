"""
infrastructure/models/resume.py

Django ORM models for the resume bounded context.
"""

import uuid

from django.db import models


class ResumeRecord(models.Model):
    resume_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate_id = models.UUIDField(db_index=True)
    raw_text = models.TextField()
    contact_email = models.CharField(max_length=254)
    contact_phone = models.CharField(max_length=50)
    contact_location = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = "resumes"
        ordering = ["-created_at"]


class ResumeSkillRecord(models.Model):
    resume = models.ForeignKey(ResumeRecord, related_name="skills", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    proficiency_level = models.CharField(max_length=20)

    class Meta:
        db_table = "resume_skills"


class ResumeExperienceRecord(models.Model):
    resume = models.ForeignKey(ResumeRecord, related_name="experiences", on_delete=models.CASCADE)
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    duration_months = models.PositiveIntegerField()
    responsibilities = models.JSONField(default=list)

    class Meta:
        db_table = "resume_experiences"


class ResumeEducationRecord(models.Model):
    resume = models.ForeignKey(ResumeRecord, related_name="education", on_delete=models.CASCADE)
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    graduation_year = models.PositiveIntegerField()

    class Meta:
        db_table = "resume_education"
