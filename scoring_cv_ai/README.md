# CV Scoring AI Service

FastAPI microservice that consumes CV scoring requests from RabbitMQ, parses PDF/DOCX files from a shared uploads volume, scores CV against job description, and publishes scoring results back to RabbitMQ.

## Environment

1. Copy `.env.example` to `.env`.
2. Fill Google AI Studio (Gemini) API key.
3. Ensure RabbitMQ is reachable from `RABBITMQ_URL`.
4. Mount shared CV uploads path so `cv_file_path` from backend is readable.

## Run Local

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5005
```

## Health

- `GET /health`

## RabbitMQ Contract

- Request routing key: `cv.scoring.request`
- Result routing key: `cv.scoring.result`
- Failed routing key: `cv.scoring.failed`

Request payload fields:

- `request_id`
- `scoring_job_id`
- `application_id`
- `job_id`
- `cv_file_path`
- `job_description`
- `min_score`
- `criteria` (optional)
