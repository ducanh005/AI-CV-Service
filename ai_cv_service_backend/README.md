# Smart Recruitment & HR Management Platform - Backend

Production-ready backend service built with FastAPI, async SQLAlchemy, PostgreSQL, JWT auth, Celery, Redis, and RabbitMQ-based async AI scoring.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- JWT (access + refresh)
- bcrypt password hashing
- Celery + Redis
- RabbitMQ (event bus for async CV scoring)
- Pydantic validation
- python-dotenv environment config
- Docker + docker-compose

## Project Structure

```text
app/
 ├── api/
 │   ├── deps.py
 │   ├── router.py
 │   └── v1/endpoints/
 ├── core/
 ├── models/
 ├── schemas/
 ├── services/
 ├── integrations/
 ├── workers/
 ├── utils/
 └── main.py
scripts/
 └── schema.sql
```

## Environment Setup

1. Copy env file:

```bash
cp .env.example .env
```

2. Update `.env` values (JWT secret, DB/Redis/RabbitMQ URLs, Gmail/LinkedIn/Google keys, AI Studio key).

## Local Run (without Docker)

1. Create virtual environment and install deps:

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

2. Ensure PostgreSQL, Redis, and RabbitMQ are running.

3. Start API:

```bash
uvicorn app.main:app --reload
```

4. Start Celery worker:

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

5. Start scoring result consumer:

```bash
python -m app.workers.scoring_result_consumer
```

## Docker Run

```bash
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Seed Sample Data

Load realistic demo data for dashboards, candidates, applications, AI scores, and interviews:

```bash
docker exec -i ai_cv_db psql -U postgres -d ai_cv_service < scripts/seed_sample_data.sql
```

Seeded test accounts (password: `Password@123`):

- HR: `hr1@example.com`, `hr2@example.com`, `hr3@example.com`
- Candidate: `candidate1@example.com` ... `candidate30@example.com`
- Admin: `admin@example.com`

## API Endpoints

### Auth

- POST `/api/v1/auth/register`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- POST `/api/v1/auth/logout`
- GET `/api/v1/auth/oauth/{provider}/authorize`
- GET `/api/v1/auth/oauth/{provider}/callback`
- POST `/api/v1/auth/oauth/{provider}/token`
- GET `/api/v1/auth/oauth/{provider}/profile`
- POST `/api/v1/auth/oauth/{provider}/register`

### Users

- GET `/api/v1/users/me`
- PATCH `/api/v1/users/me`
- POST `/api/v1/users/me/avatar`
- POST `/api/v1/users/me/change-password`

### Companies

- POST `/api/v1/companies`
- GET `/api/v1/companies/{company_id}`
- PATCH `/api/v1/companies/{company_id}`

### Jobs

- POST `/api/v1/jobs`
- GET `/api/v1/jobs`
- PATCH `/api/v1/jobs/{job_id}`
- DELETE `/api/v1/jobs/{job_id}`

### CV

- POST `/api/v1/cvs/upload`

### AI

- POST `/api/v1/ai/score-cv`
- POST `/api/v1/ai/rank-candidates`
- POST `/api/v1/ai/rank-candidates/async`
- GET `/api/v1/ai/rank-candidates/async/{scoring_job_id}`

### Applications

- POST `/api/v1/applications`
- GET `/api/v1/applications/job/{job_id}`
- PATCH `/api/v1/applications/{application_id}/review`

### Interviews

- POST `/api/v1/interviews`

### Integrations

- GET `/api/v1/integrations/linkedin/oauth-url`
- GET `/api/v1/integrations/linkedin/callback`
- POST `/api/v1/integrations/gmail/test-email`
- POST `/api/v1/integrations/calendar/test-event`

## Notes

- Role values: `user`, `hr`, `admin`
- Jobs/Companies/Users implement soft-delete fields where needed.
- CV upload now extracts text from PDF/DOCX files for downstream AI scoring.
- AI screening supports HR criteria (`required_skills`, `preferred_skills`, `education_keywords`, `min_years_experience`) via Google AI Studio (Gemini) only.
- HR/Admin can rank and filter candidates for a job by score threshold using `/api/v1/ai/rank-candidates` and optionally trigger automatic screening result emails.
- Async AI scoring flow uses RabbitMQ and stores per-request progress in DB tables (`scoring_jobs`, `scoring_job_items`).
- Database schema SQL is provided in `scripts/schema.sql`.
