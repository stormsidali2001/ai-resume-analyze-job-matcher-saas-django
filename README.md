# ResumeAI

An intelligent resume analyzer and job matching platform built with **Django REST Framework**, **Next.js**, **Celery**, **Redis**, **Django Channels**, and **Clean Architecture / Domain-Driven Design**.

---

## Architecture

```
resume-analyzer/
├── api/                        # Python backend
│   ├── domain/                 # Pure Python domain layer (no framework imports)
│   ├── application/            # Use cases, DTOs, ports
│   ├── infrastructure/         # Django ORM models, repositories, mappers, Celery tasks
│   ├── interfaces/             # DRF ViewSets, serializers, URL routing
│   ├── config/                 # Django settings, Celery app, URLs
│   └── manage.py
├── frontend/                   # Next.js frontend
└── docker-compose.yml          # PostgreSQL + Redis
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose

---

## Backend setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd resume-analyzer
```

### 2. Start infrastructure (PostgreSQL + Redis)

```bash
docker compose up -d
```

This starts two containers:

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| PostgreSQL 16 | `resumeai_db` | `5432` | Primary database |
| Redis 7 | `resumeai_redis` | `6379` | Celery broker + result backend + Django cache + WebSocket channel layer |

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

The defaults in `.env.example` match the Docker Compose config, so no changes are needed for local development. To enable Gemini AI analysis, add your API key:

```
GEMINI_API_KEY=your-key-here
```

Without it the system falls back to keyword-based extraction (fully functional, just less accurate).

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the Django development server

```bash
python manage.py runserver
```

The API is now available at `http://localhost:8000`. WebSocket connections are handled at `ws://localhost:8000/ws/resume/{id}/`.

> **Django Channels note:** `daphne` is the first entry in `INSTALLED_APPS`, which automatically upgrades `manage.py runserver` to an ASGI-capable server. No separate process is needed for WebSockets in development.

### 7. Start the Celery worker

Celery runs as a **separate process** alongside Django — it picks up background tasks (AI resume analysis) from the Redis queue.

Open a second terminal in the `api/` directory:

```bash
cd api
source .venv/bin/activate
celery -A config worker -l info
```

You should see output like:

```
[config] Celery 5.x.x  ...
[config] Connected to redis://localhost:6379/0
[config] Ready.
```

> **Why a separate process?** Celery workers pull tasks off a queue independently of the HTTP server. Django enqueues the task with a single `.delay()` call and responds immediately (202). The worker does the slow Gemini API call in the background, then broadcasts status updates to any connected WebSocket clients via Django Channels.

When a resume is uploaded or analyzed, `analysis_status` transitions through:

```
pending → processing → done
                     ↘ failed  (retries up to 3× with exponential back-off)
```

Each transition is pushed over WebSocket to the browser in real time — the frontend React Query cache updates automatically and the skills section populates without a page refresh.

---

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The app is available at `http://localhost:3000`.

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
| `POST` | `/api/v1/resumes/` | Create a resume from text — returns `202`, AI analysis runs in background |
| `POST` | `/api/v1/resumes/upload/` | Upload a PDF — returns `202`, AI analysis runs in background |
| `GET` | `/api/v1/resumes/{id}/` | Get a resume (poll this for `analysis_status`) |
| `PATCH` | `/api/v1/resumes/{id}/` | Update resume text |
| `POST` | `/api/v1/resumes/{id}/analyze/` | Queue a re-analysis — returns `202` immediately |
| `POST` | `/api/v1/resumes/{id}/skills/` | Add a skill manually |
| `POST` | `/api/v1/resumes/{id}/archive/` | Archive a resume |

### Jobs (read is public, write requires authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/jobs/` | List published jobs — cached in Redis for 5 min |
| `POST` | `/api/v1/jobs/` | Create a job posting |
| `GET` | `/api/v1/jobs/{id}/` | Get a job |
| `GET` | `/api/v1/jobs/mine/` | List your own jobs (any status) |
| `POST` | `/api/v1/jobs/{id}/skills/` | Add a required skill |
| `POST` | `/api/v1/jobs/{id}/publish/` | Publish a job (invalidates jobs cache) |
| `POST` | `/api/v1/jobs/{id}/close/` | Close a job (invalidates jobs cache) |

### Matching (authentication required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/match/` | Match a resume against a job — result cached in Redis for 1 hour |
| `POST` | `/api/v1/match/batch/` | Match one resume against up to 10 jobs concurrently (asyncio) |

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

# 3. Create a resume (returns 202 — AI analysis queued in background)
curl -s -X POST $BASE/api/v1/resumes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Senior Python engineer with 7 years of experience building REST APIs with Django and FastAPI. Expert in distributed systems, PostgreSQL, and cloud deployments.",
    "email": "alice@example.com",
    "phone": "+1-555-0100",
    "location": "New York, NY"
  }' | python3 -m json.tool

RESUME_ID=<paste resume_id from above>

# 4. Poll until analysis_status is "done"
curl -s $BASE/api/v1/resumes/$RESUME_ID/ \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['analysis_status'], '-', len(r['skills']), 'skills')"

# 5. Register a recruiter and create a job
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
    "description": "We need a Senior Python Engineer to architect backend systems, build scalable REST APIs, and mentor junior developers.",
    "city": "New York",
    "country": "USA",
    "employment_type": "full_time",
    "required_experience_months": 48
  }')

JOB_ID=$(echo $JOB | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

# 6. Add a required skill and publish
curl -s -X POST $BASE/api/v1/jobs/$JOB_ID/skills/ \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Python","category":"programming","proficiency_level":"expert"}'

curl -s -X POST $BASE/api/v1/jobs/$JOB_ID/publish/ \
  -H "Authorization: Bearer $RECRUITER_TOKEN"

# 7. Match the resume to the job
curl -s -X POST $BASE/api/v1/match/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\":\"$RESUME_ID\",\"job_id\":\"$JOB_ID\"}" \
  | python3 -m json.tool

# 8. Batch match against multiple jobs (concurrent asyncio fetch)
curl -s -X POST $BASE/api/v1/match/batch/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"resume_id\":\"$RESUME_ID\",\"job_ids\":[\"$JOB_ID\"]}" \
  | python3 -m json.tool
```

---

## Seeding demo data

The `seed` management command populates the database with realistic demo users, resumes, and job postings.

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

Usernames follow the pattern `candidate_<name>` and `recruiter_<name>`. To list them, log in to the Django admin at `http://localhost:8000/admin/` using a superuser account.

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
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL (Celery broker, Django cache, channel layer) |
| `GEMINI_API_KEY` | _(empty)_ | Google Gemini API key — enables AI resume parsing |

---

## Stopping services

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers and delete all data
```
