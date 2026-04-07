from datetime import datetime, timezone

from pydantic import BaseModel, Field


class HRScoreCriteria(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    education_keywords: list[str] = Field(default_factory=list)
    min_years_experience: int | None = Field(default=None, ge=0)
    skill_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    experience_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    education_weight: float = Field(default=0.15, ge=0.0, le=1.0)


class ScoringRequestPayload(BaseModel):
    request_id: str
    scoring_job_id: str
    application_id: int
    job_id: int
    cv_file_path: str
    job_description: str = Field(min_length=10)
    min_score: float = Field(default=60.0, ge=0.0, le=100.0)
    criteria: HRScoreCriteria | None = None
    requested_by: int | None = None


class ScoringResultPayload(BaseModel):
    request_id: str
    scoring_job_id: str
    application_id: int
    job_id: int
    score: float = Field(ge=0.0, le=100.0)
    reasoning: str
    provider: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ScoringFailedPayload(BaseModel):
    request_id: str
    scoring_job_id: str
    application_id: int
    job_id: int
    error: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
