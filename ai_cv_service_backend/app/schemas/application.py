from pydantic import BaseModel
from datetime import datetime

from app.models.enums import ApplicationStatus


class ApplyJobRequest(BaseModel):
    job_id: int
    cv_id: int


class ApplicationReviewRequest(BaseModel):
    status: ApplicationStatus
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    cv_id: int | None
    reviewed_by: int | None
    status: ApplicationStatus
    notes: str | None
    created_at: datetime | None = None
    candidate_name: str | None = None
    candidate_email: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    ai_score: float | None = None
    cv_file_name: str | None = None
    cv_file_path: str | None = None
    cv_mime_type: str | None = None
