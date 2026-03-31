# AI CV Service - Setup Guide

Huong dan nhanh de chay du an sau khi clone.

## 1) Yeu cau moi truong

- Git
- Python 3.11+ (khuyen nghi)
- Node.js 18+ va npm
- Docker Desktop (neu muon chay bang Docker)
- PostgreSQL + Redis (neu chay local khong Docker)

## 2) Clone project

```bash
git clone <repo-url>
cd "AI CV Service"
```

## 3) Setup Backend (FastAPI)

Di vao backend:

```bash
cd ai_cv_service_backend
```

Tao env va cai thu vien:

```bash
python -m venv .venv
# Windows Git Bash
source .venv/Scripts/activate
# Neu dung PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Tao file env:

```bash
cp .env.example .env
```

Cap nhat cac bien trong `.env`:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- Cac khoa tich hop (Gmail/LinkedIn/Google Calendar/AI) neu can

### Chay backend local

```bash
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

### Chay Celery worker (neu can background jobs)

Mo terminal moi trong `ai_cv_service_backend`:

```bash
source .venv/Scripts/activate
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

## 4) Setup Frontend (React + Vite)

Tu thu muc goc project:

```bash
cd ai_cv_service_frontend
npm install
```

Tao file env cho frontend:

```bash
cp .env.example .env
```

Neu can, sua:

- `VITE_API_BASE_URL=http://localhost:8000/api/v1`

Chay frontend:

```bash
npm run dev
```

Frontend local: http://localhost:5173

## 5) Chay bang Docker (khuyen nghi cho moi truong dong bo)

Tu thu muc `ai_cv_service_backend`:

```bash
docker compose up --build
```

API: http://localhost:8000
Swagger: http://localhost:8000/docs

## 6) Seed du lieu mau (tuy chon)

Tu thu muc `ai_cv_service_backend`:

```bash
docker exec -i ai_cv_db psql -U postgres -d ai_cv_service < scripts/seed_sample_data.sql
```

Tai khoan test (password: `Password@123`):

- HR: `hr1@example.com`, `hr2@example.com`, `hr3@example.com`
- Candidate: `candidate1@example.com` ... `candidate30@example.com`
- Admin: `admin@example.com`

## 7) Thu tu chay de dev nhanh

1. Chay backend (`uvicorn ...`)
2. Chay worker (neu can)
3. Chay frontend (`npm run dev`)
4. Truy cap frontend va dang nhap test account

## 8) Loi thuong gap

- Frontend khong goi duoc API: kiem tra `VITE_API_BASE_URL`.
- Loi CORS: kiem tra cau hinh CORS trong backend env/config.
- Dang nhap loi 401 lien tuc: xoa localStorage va dang nhap lai.
- Worker khong nhan task: kiem tra Redis va command Celery.
