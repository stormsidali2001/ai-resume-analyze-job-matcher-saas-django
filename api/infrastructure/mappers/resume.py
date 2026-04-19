"""
infrastructure/mappers/resume.py

Bidirectional mapping between ResumeRecord (ORM) and ResumeAggregate (domain).
"""

from __future__ import annotations

from domain.resume.aggregate import ResumeAggregate
from domain.resume.value_objects import ContactInfo, Education, Experience, RawResumeContent
from domain.common.value_objects import Skill
from infrastructure.models.resume import (
    ResumeEducationRecord,
    ResumeExperienceRecord,
    ResumeRecord,
    ResumeSkillRecord,
)


class ResumeMapper:
    @staticmethod
    def to_aggregate(record: ResumeRecord) -> ResumeAggregate:
        """Hydrate a ResumeRecord (with prefetched relations) into a ResumeAggregate."""
        resume = ResumeAggregate(
            resume_id=str(record.resume_id),
            candidate_id=str(record.candidate_id),
            raw_text=RawResumeContent(text=record.raw_text),
            contact_info=ContactInfo(
                email=record.contact_email,
                phone=record.contact_phone,
                location=record.contact_location,
            ),
        )
        # Restore internal mutable state directly to avoid re-running validations
        resume._status = record.status
        resume._analysis_status = record.analysis_status
        resume._created_at = record.created_at
        resume._updated_at = record.updated_at

        for skill_rec in record.skills.all():
            resume.add_skill(
                Skill(
                    name=skill_rec.name,
                    category=skill_rec.category,
                    proficiency_level=skill_rec.proficiency_level,
                )
            )

        for exp_rec in record.experiences.all():
            resume.add_experience(
                Experience(
                    role=exp_rec.role,
                    company=exp_rec.company,
                    duration_months=exp_rec.duration_months,
                    responsibilities=exp_rec.responsibilities,
                )
            )

        for edu_rec in record.education.all():
            resume.add_education(
                Education(
                    degree=edu_rec.degree,
                    institution=edu_rec.institution,
                    graduation_year=edu_rec.graduation_year,
                )
            )

        return resume

    @staticmethod
    def update_record(record: ResumeRecord, resume: ResumeAggregate) -> None:
        """Sync scalar fields from the aggregate onto the ORM record."""
        record.candidate_id = resume.candidate_id
        record.raw_text = resume.raw_text.text
        record.contact_email = resume.contact_info.email
        record.contact_phone = resume.contact_info.phone
        record.contact_location = resume.contact_info.location
        record.status = resume.status
        record.analysis_status = resume.analysis_status
        record.created_at = resume.created_at
        record.updated_at = resume.updated_at

    @staticmethod
    def sync_related(record: ResumeRecord, resume: ResumeAggregate) -> None:
        """Delete-and-recreate all related records from the aggregate's current state."""
        record.skills.all().delete()
        ResumeSkillRecord.objects.bulk_create([
            ResumeSkillRecord(
                resume=record,
                name=s.name,
                category=s.category,
                proficiency_level=s.proficiency_level,
            )
            for s in resume.skills
        ])

        record.experiences.all().delete()
        ResumeExperienceRecord.objects.bulk_create([
            ResumeExperienceRecord(
                resume=record,
                role=e.role,
                company=e.company,
                duration_months=e.duration_months,
                responsibilities=list(e.responsibilities),
            )
            for e in resume.experiences
        ])

        record.education.all().delete()
        ResumeEducationRecord.objects.bulk_create([
            ResumeEducationRecord(
                resume=record,
                degree=ed.degree,
                institution=ed.institution,
                graduation_year=ed.graduation_year,
            )
            for ed in resume.education
        ])
