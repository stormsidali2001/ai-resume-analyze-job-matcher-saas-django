# ResumeAI

An intelligent resume analyzer and job matching platform built with **Django REST Framework**, **Clean Architecture**, and **Domain-Driven Design**.

---

## Architecture

```
resume-analyzer/
├── api/                        # Python backend
│   ├── domain/                 # Pure Python domain layer (no framework imports)
│   ├── application/            # Use cases, DTOs, ports
│   ├── infrastructure/         # Django ORM models, repositories, mappers
│   ├── interfaces/             # DRF ViewSets, serializers, URL routing
│   ├── config/                 # Django settings, URLs
│   ├── tests/                  # Full test suite (478 tests)
│   └── manage.py
├── frontend/                   # Next.js (coming soon)
└── docker-compose.yml          # PostgreSQL database
```

---

## Prerequisites

- Python 3.11+
- Docker and Docker Compose

---

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd resume-analyzer
```

### 2. Start the database

```bash
docker compose up -d
```

This starts a PostgreSQL 16 container at `localhost:5432` with:
- Database: `resumeai`
- User: `postgres`
- Password: `postgres`

### 3. Create the Python virtual environment

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

The defaults in `.env.example` match the Docker Compose database config, so no changes are needed for local development.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (optional, for Django admin)

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

The API is now available at `http://localhost:8000`.

---

## API Documentation

Interactive docs are served automatically when the development server is running:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/docs/` | Swagger UI — try requests directly in the browser |
| `http://localhost:8000/api/redoc/` | ReDoc — clean, readable reference |
| `http://localhost:8000/api/schema/` | Raw OpenAPI 3.0 schema (YAML) |

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Register a new user (returns JWT tokens) |
| `POST` | `/api/auth/token/` | Obtain access + refresh tokens |
| `POST` | `/api/auth/token/refresh/` | Refresh access token |

### Resumes (authentication required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/resumes/` | List your resumes |
| `POST` | `/api/v1/resumes/` | Create a resume |
| `GET` | `/api/v1/resumes/{id}/` | Get a resume |
| `PATCH` | `/api/v1/resumes/{id}/` | Update resume text |
| `POST` | `/api/v1/resumes/{id}/analyze/` | Extract skills from text |
| `POST` | `/api/v1/resumes/{id}/skills/` | Add a skill manually |
| `POST` | `/api/v1/resumes/{id}/archive/` | Archive a resume |

### Jobs (read is public, write requires authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/jobs/` | List published jobs (public) |
| `POST` | `/api/v1/jobs/` | Create a job posting |
| `GET` | `/api/v1/jobs/{id}/` | Get a job (public) |
| `POST` | `/api/v1/jobs/{id}/skills/` | Add a required skill |
| `POST` | `/api/v1/jobs/{id}/publish/` | Publish a job |
| `POST` | `/api/v1/jobs/{id}/close/` | Close a job |

### Matching (authentication required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/match/` | Match a resume against a job posting |

---

## Quick API walkthrough

```bash
BASE=http://localhost:8000

# 1. Register a candidate
curl -s -X POST $BASE/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"Str0ngPass!99","role":"candidate"}' \
  | python3 -m json.tool

# 2. Save the access token
TOKEN=<paste access token here>

# 3. Create a resume
curl -s -X POST $BASE/api/v1/resumes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Senior Python engineer with 7 years of experience building REST APIs with Django and FastAPI. Expert in distributed systems, PostgreSQL, and cloud deployments.",
    "email": "alice@example.com",
    "phone": "+1-555-0100",
    "location": "New York, NY"
  }' | python3 -m json.tool

# 4. Register a recruiter and create a job
curl -s -X POST $BASE/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","email":"bob@example.com","password":"Str0ngPass!99","role":"recruiter"}' \
  | python3 -m json.tool

RECRUITER_TOKEN=<paste recruiter access token>

JOB=$(curl -s -X POST $BASE/api/v1/jobs/ \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Engineer",
    "company": "TechCorp",
    "description": "We need a Senior Python Engineer to architect backend systems, build scalable REST APIs, and mentor junior developers on best practices.",
    "city": "New York",
    "country": "USA",
    "employment_type": "full_time",
    "required_experience_months": 48
  }')

JOB_ID=$(echo $JOB | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

# 5. Add a required skill and publish
curl -s -X POST $BASE/api/v1/jobs/$JOB_ID/skills/ \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Python","category":"programming","proficiency_level":"expert"}'

curl -s -X POST $BASE/api/v1/jobs/$JOB_ID/publish/ \
  -H "Authorization: Bearer $RECRUITER_TOKEN"

# 6. Match the resume to the job
RESUME_ID=<paste resume id from step 3>

curl -s -X POST $BASE/api/v1/match/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\":\"$RESUME_ID\",\"job_id\":\"$JOB_ID\"}" \
  | python3 -m json.tool
```

---

## Seeding demo data

he `seed` management command populates the database with realistic demo users, resumes, and job postings.

```bash
# Default: 5 candidates + 3 recruiters
python manage.py seed

# Custom counts
python manage.py seed --candidates 10 --recruiters 5

# Wipe existing seed data and re-seed
python manage.py seed --reset
```

**What gets created:**

| Type | Count (default) | Details |
|------|-----------------|---------|
| Candidate users | 5 | Each with a resume and 4–7 randomly assigned skills |
| Recruiter users | 3 | Each with 1–2 job postings (first is always published, rest are drafts) |

All seed users share the same password: **`Password123!`**

Usernames follow the pattern `candidate_<name>` and `recruiter_<name>`. To list them after seeding, log in to the Django admin at `http://localhost:8000/admin/` using a superuser account.

**Job roles seeded:**

| Role | Required experience |
|------|-------------------|
| Senior Python Engineer | 4 years |
| Backend Engineer | 2 years |
| Full-Stack Engineer | 2 years |
| DevOps Engineer | 3 years |
| Data Engineer | 2.5 years |

**Skills pool** (20 skills across 8 categories):

| Category | Skills |
|----------|--------|
| Programming | Python, TypeScript, Go |
| Framework | Django, FastAPI, Celery |
| Database | PostgreSQL, Redis, Elasticsearch |
| DevOps | Docker, Kubernetes, CI/CD |
| Cloud | AWS |
| Frontend | React |
| Architecture | REST APIs, GraphQL |
| Tooling | Git, Linux |

**Companies** used in job postings: FinStack (London), DataSphere (Berlin), CloudNative (Amsterdam), ByteForge (New York), Nexus AI (San Francisco), PulseHQ (Paris).

Obtain a token to start exploring:
```bash
curl -s -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "<seed-username>", "password": "Password123!"}' \
  | python3 -m json.tool
```

---

## Running tests

```bash
cd api
source .venv/bin/activate

# Full suite (requires the database to be running)
pytest tests/

# Domain and application only (no database needed)
pytest tests/domain/ tests/application/

# Infrastructure and API only
pytest tests/infrastructure/ tests/interfaces/

# With coverage report
pytest tests/ --cov --cov-report=term-missing
```

Current status: **478 tests, 0 failures**.

---

## Environment variables

All variables are read from `api/.env`. See `api/.env.example` for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Django debug mode |
| `SECRET_KEY` | `insecure-dev-key-...` | Django secret key — change in production |
| `DB_NAME` | `resumeai` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |

---

## Stopping the database

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers and delete all data
```
