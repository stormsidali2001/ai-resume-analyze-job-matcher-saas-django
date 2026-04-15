"""
infrastructure/models/job.py

Django ORM models for the job bounded context.
"""

import uuid

from django.db import models


class JobRecord(models.Model):
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recruiter_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    location_city = models.CharField(max_length=100)
    location_country = models.CharField(max_length=100)
    location_remote = models.BooleanField(default=False)
    employment_type = models.CharField(max_length=20)
    required_experience_months = models.PositiveIntegerField(default=0)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField()

    class Meta:
        db_table = "jobs"
        ordering = ["-created_at"]


class JobSkillRecord(models.Model):
    job = models.ForeignKey(JobRecord, related_name="required_skills", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    proficiency_level = models.CharField(max_length=20)

    class Meta:
        db_table = "job_skills"
