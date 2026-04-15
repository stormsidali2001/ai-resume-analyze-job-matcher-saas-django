"""
infrastructure/management/commands/seed.py

Populate the database with realistic demo data.

The seeder is intentionally infrastructure-agnostic: it only depends on
application-layer use cases and DTOs. Any change to the ORM schema is
transparent here because all persistence goes through the use cases.

Usage:
    python manage.py seed                   # default: 5 candidates, 3 recruiters
    python manage.py seed --candidates 10 --recruiters 5
    python manage.py seed --reset           # wipe seed data first, then re-seed
"""

from __future__ import annotations

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

from application.job.dtos import AddSkillToJobCommand, CreateJobCommand, SalaryRangeDTO
from application.job.use_cases import (
    AddRequiredSkillToJobUseCase,
    CreateJobUseCase,
    PublishJobUseCase,
)
from application.resume.dtos import AddSkillCommand, AnalyzeResumeCommand, CreateResumeCommand
from application.resume.use_cases import AddSkillToResumeUseCase, AnalyzeResumeUseCase, CreateResumeUseCase
from application.user.dtos import CreateUserCommand
from application.user.use_cases import CreateUserUseCase
from domain.user.exceptions import UserAlreadyExistsError
from interfaces.api.dependencies import get_job_use_cases, get_resume_use_cases, get_user_use_cases

User = get_user_model()
fake = Faker()
Faker.seed(42)
random.seed(42)

# ── Static data pools ──────────────────────────────────────────────────────────

TECH_SKILLS: list[dict] = [
    {"name": "Python",          "category": "programming",   "proficiency_level": "expert"},
    {"name": "Django",          "category": "framework",     "proficiency_level": "advanced"},
    {"name": "FastAPI",         "category": "framework",     "proficiency_level": "intermediate"},
    {"name": "PostgreSQL",      "category": "database",      "proficiency_level": "advanced"},
    {"name": "Redis",           "category": "database",      "proficiency_level": "intermediate"},
    {"name": "Docker",          "category": "devops",        "proficiency_level": "advanced"},
    {"name": "Kubernetes",      "category": "devops",        "proficiency_level": "intermediate"},
    {"name": "AWS",             "category": "cloud",         "proficiency_level": "advanced"},
    {"name": "React",           "category": "frontend",      "proficiency_level": "intermediate"},
    {"name": "TypeScript",      "category": "programming",   "proficiency_level": "advanced"},
    {"name": "Go",              "category": "programming",   "proficiency_level": "intermediate"},
    {"name": "REST APIs",       "category": "architecture",  "proficiency_level": "expert"},
    {"name": "GraphQL",         "category": "architecture",  "proficiency_level": "intermediate"},
    {"name": "CI/CD",           "category": "devops",        "proficiency_level": "advanced"},
    {"name": "Git",             "category": "tooling",       "proficiency_level": "expert"},
    {"name": "Linux",           "category": "tooling",       "proficiency_level": "advanced"},
    {"name": "Machine Learning","category": "data-science",  "proficiency_level": "intermediate"},
    {"name": "Pandas",          "category": "data-science",  "proficiency_level": "advanced"},
    {"name": "Celery",          "category": "framework",     "proficiency_level": "intermediate"},
    {"name": "Elasticsearch",   "category": "database",      "proficiency_level": "intermediate"},
]

JOB_ROLES: list[dict] = [
    {
        "title": "Senior Python Engineer",
        "description": (
            "We are looking for a Senior Python Engineer to join our backend team. "
            "You will design and implement scalable REST APIs, own critical infrastructure, "
            "and mentor junior engineers. You will work closely with product and data teams "
            "to ship high-quality features in a fast-paced environment. "
            "Strong experience with Django or FastAPI is essential, along with solid "
            "knowledge of PostgreSQL, Redis, and cloud platforms such as AWS."
        ),
        "required_skills": ["Python", "Django", "PostgreSQL", "REST APIs", "Docker"],
        "required_experience_months": 48,
    },
    {
        "title": "Backend Engineer",
        "description": (
            "Join our engineering team as a Backend Engineer and help us build the next "
            "generation of our platform. You will develop robust microservices, improve "
            "system reliability, and collaborate with front-end and DevOps teams. "
            "We value clean code, thorough testing, and a pragmatic approach to architecture. "
            "Experience with Python and cloud technologies is a must."
        ),
        "required_skills": ["Python", "REST APIs", "PostgreSQL", "Docker", "AWS"],
        "required_experience_months": 24,
    },
    {
        "title": "Full-Stack Engineer",
        "description": (
            "We need a versatile Full-Stack Engineer who is comfortable on both the front "
            "and back end. You will build user-facing features with React and TypeScript, "
            "and implement the supporting APIs in Python. "
            "You should be confident working across the stack and excited to take ownership "
            "of features end-to-end. Experience with modern CI/CD pipelines is a bonus."
        ),
        "required_skills": ["Python", "React", "TypeScript", "REST APIs", "Git"],
        "required_experience_months": 24,
    },
    {
        "title": "DevOps Engineer",
        "description": (
            "We are hiring a DevOps Engineer to strengthen our infrastructure and deployment "
            "pipelines. You will manage Kubernetes clusters, improve observability, and drive "
            "automation across the engineering organisation. "
            "You will partner with software engineers to ensure systems are reliable, secure, "
            "and cost-efficient at scale. Experience with AWS and Terraform is preferred."
        ),
        "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux"],
        "required_experience_months": 36,
    },
    {
        "title": "Data Engineer",
        "description": (
            "We are looking for a Data Engineer to build and maintain our data pipelines and "
            "warehouse infrastructure. You will work closely with analysts and data scientists "
            "to ensure clean, reliable data is available when they need it. "
            "Strong Python skills and experience with Pandas, Celery, and Elasticsearch are "
            "highly desirable. A background in distributed data processing is a plus."
        ),
        "required_skills": ["Python", "Pandas", "PostgreSQL", "Celery", "Elasticsearch"],
        "required_experience_months": 30,
    },
]

COMPANIES = [
    ("FinStack",     "London",        "GB"),
    ("DataSphere",   "Berlin",        "DE"),
    ("CloudNative",  "Amsterdam",     "NL"),
    ("ByteForge",    "New York",      "US"),
    ("Nexus AI",     "San Francisco", "US"),
    ("PulseHQ",      "Paris",         "FR"),
]

DEGREES = [
    "BSc Computer Science",
    "MSc Software Engineering",
    "BSc Information Technology",
    "MEng Computer Engineering",
    "BSc Mathematics",
]

EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "freelance", "internship"]


# ── Resume text builder ────────────────────────────────────────────────────────

def _resume_text(name: str, skill_names: list[str], exp_years: int, role: str) -> str:
    """Build a rich raw text that passes RawResumeContent's 50-char minimum."""
    skills_line = ", ".join(skill_names[:6])
    return (
        f"{name} is a software professional with {exp_years} years of experience as {role}. "
        f"Core skills include {skills_line}. "
        f"Has delivered production-grade systems across startups and scale-ups, "
        f"working in distributed, remote-friendly teams. "
        f"Holds a {random.choice(DEGREES)} and has contributed to open-source projects. "
        f"Passionate about clean architecture, test-driven development, and continuous delivery. "
        f"Comfortable with agile methodologies and cross-functional collaboration."
    )


# ── Seeder classes ─────────────────────────────────────────────────────────────

class CandidateSeeder:
    def __init__(self, user_use_cases: dict, resume_use_cases: dict, stdout) -> None:
        self._create_user: CreateUserUseCase = user_use_cases["create"]
        self._create: CreateResumeUseCase = resume_use_cases["create"]
        self._add_skill: AddSkillToResumeUseCase = resume_use_cases["add_skill"]
        self._out = stdout

    def seed(self, n: int) -> None:
        for _ in range(n):
            user_dto = self._make_user()
            resume_dto = self._create_resume(user_dto)
            skills = self._pick_skills(random.randint(4, 7))
            self._add_skills(resume_dto.resume_id, user_dto.id, skills)
            self._out.write(
                f"  candidate: {user_dto.username} "
                f"→ resume with {len(skills)} skills"
            )

    # -- private --

    def _make_user(self):
        first_name = fake.first_name()
        last_name = fake.last_name()
        cmd = CreateUserCommand(
            username=f"candidate_{fake.unique.user_name()}",
            email=fake.email(),
            password="Password123!",
            role="candidate",
            first_name=first_name,
            last_name=last_name,
        )
        try:
            return self._create_user.execute(cmd)
        except UserAlreadyExistsError:
            # Retry with a fresh unique name (e.g. when re-seeding without --reset)
            cmd = CreateUserCommand(
                username=f"candidate_{fake.unique.user_name()}",
                email=fake.email(),
                password="Password123!",
                role="candidate",
                first_name=first_name,
                last_name=last_name,
            )
            return self._create_user.execute(cmd)

    def _create_resume(self, user_dto) -> object:
        skills = self._pick_skills(5)
        exp_years = random.randint(1, 8)
        full_name = f"{user_dto.username}"
        raw_text = _resume_text(
            full_name,
            [s["name"] for s in skills],
            exp_years,
            fake.job(),
        )
        cmd = CreateResumeCommand(
            candidate_id=user_dto.id,
            raw_text=raw_text,
            email=user_dto.email,
            phone=fake.phone_number()[:50],
            location=fake.city(),
        )
        return self._create.execute(cmd)

    def _pick_skills(self, n: int) -> list[dict]:
        return random.sample(TECH_SKILLS, min(n, len(TECH_SKILLS)))

    def _add_skills(self, resume_id: str, candidate_id: str, skills: list[dict]) -> None:
        for skill in skills:
            cmd = AddSkillCommand(
                resume_id=resume_id,
                candidate_id=candidate_id,
                name=skill["name"],
                category=skill["category"],
                proficiency_level=skill["proficiency_level"],
            )
            self._add_skill.execute(cmd)


class RecruiterSeeder:
    def __init__(self, user_use_cases: dict, job_use_cases: dict, stdout) -> None:
        self._create_user: CreateUserUseCase = user_use_cases["create"]
        self._create: CreateJobUseCase = job_use_cases["create"]
        self._add_skill: AddRequiredSkillToJobUseCase = job_use_cases["add_skill"]
        self._publish: PublishJobUseCase = job_use_cases["publish"]
        self._out = stdout

    def seed(self, n: int) -> None:
        company_pool = list(COMPANIES)
        random.shuffle(company_pool)

        for i in range(n):
            user_dto = self._make_user()
            company = company_pool[i % len(company_pool)]
            n_jobs = random.randint(1, 2)

            for j in range(n_jobs):
                role = random.choice(JOB_ROLES)
                publish = (j == 0)   # always publish the first job per recruiter
                job_dto = self._create_job(user_dto, role, company)
                self._add_skills(job_dto.job_id, user_dto.id, role["required_skills"])
                if publish:
                    self._publish.execute(job_dto.job_id, user_dto.id)
                job_status = "PUBLISHED" if publish else "DRAFT"
                self._out.write(
                    f"  recruiter: {user_dto.username} "
                    f"→ [{job_status}] {role['title']} @ {company[0]}"
                )

    # -- private --

    def _make_user(self):
        cmd = CreateUserCommand(
            username=f"recruiter_{fake.unique.user_name()}",
            email=fake.company_email(),
            password="Password123!",
            role="recruiter",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        try:
            return self._create_user.execute(cmd)
        except UserAlreadyExistsError:
            cmd = CreateUserCommand(
                username=f"recruiter_{fake.unique.user_name()}",
                email=fake.company_email(),
                password="Password123!",
                role="recruiter",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            return self._create_user.execute(cmd)

    def _create_job(self, user_dto, role: dict, company: tuple) -> object:
        company_name, city, country = company
        salary_min = random.choice([60_000, 70_000, 80_000, 90_000, 100_000])
        salary_max = salary_min + random.choice([15_000, 20_000, 30_000, 40_000])

        cmd = CreateJobCommand(
            recruiter_id=user_dto.id,
            title=role["title"],
            company=company_name,
            description=role["description"],
            city=city,
            country=country,
            remote=random.random() > 0.5,
            employment_type=random.choice(EMPLOYMENT_TYPES),
            required_experience_months=role["required_experience_months"],
            salary_range=SalaryRangeDTO(
                min_salary=salary_min,
                max_salary=salary_max,
                currency="USD",
            ),
        )
        return self._create.execute(cmd)

    def _add_skills(self, job_id: str, recruiter_id: str, skill_names: list[str]) -> None:
        skill_map = {s["name"]: s for s in TECH_SKILLS}
        for name in skill_names:
            skill = skill_map[name]
            cmd = AddSkillToJobCommand(
                job_id=job_id,
                recruiter_id=recruiter_id,
                name=skill["name"],
                category=skill["category"],
                proficiency_level=skill["proficiency_level"],
            )
            self._add_skill.execute(cmd)


# ── Management command ─────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed the database with realistic demo data."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--candidates",
            type=int,
            default=5,
            help="Number of candidate users to create (default: 5).",
        )
        parser.add_argument(
            "--recruiters",
            type=int,
            default=3,
            help="Number of recruiter users to create (default: 3).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing seed users and their data before seeding.",
        )

    def handle(self, *args, **options) -> None:
        if options["reset"]:
            self._reset()

        n_candidates = options["candidates"]
        n_recruiters = options["recruiters"]

        user_use_cases = get_user_use_cases()

        self.stdout.write(self.style.MIGRATE_HEADING("\n── Seeding candidates ──"))
        CandidateSeeder(user_use_cases, get_resume_use_cases(), self.stdout).seed(n_candidates)

        self.stdout.write(self.style.MIGRATE_HEADING("\n── Seeding recruiters ──"))
        RecruiterSeeder(user_use_cases, get_job_use_cases(), self.stdout).seed(n_recruiters)

        total = n_candidates + n_recruiters
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Done — {total} users "
            f"({n_candidates} candidates, {n_recruiters} recruiters)\n"
            f"  Password for all seed users: Password123!\n"
            f"  Obtain a token:  POST /api/auth/token/\n"
        ))

    def _reset(self) -> None:
        self.stdout.write(self.style.WARNING("\n── Resetting seed data ──"))
        deleted_c, _ = User.objects.filter(username__startswith="candidate_").delete()
        deleted_r, _ = User.objects.filter(username__startswith="recruiter_").delete()
        self.stdout.write(f"  Deleted {deleted_c + deleted_r} seed users (cascaded resumes/jobs).")
        fake.unique.clear()
