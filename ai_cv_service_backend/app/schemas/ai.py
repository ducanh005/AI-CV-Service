from datetime import datetime

from pydantic import BaseModel, Field


class HRScoreCriteria(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    education_keywords: list[str] = Field(default_factory=list)
    min_years_experience: int | None = Field(default=None, ge=0)
    skill_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    experience_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    education_weight: float = Field(default=0.15, ge=0.0, le=1.0)


class ScoreCVRequest(BaseModel):
    application_id: int | None = None
    cv_id: int | None = None
    cv_text: str | None = Field(default=None, min_length=10)
    job_description: str | None = Field(default=None, min_length=10)
    criteria: HRScoreCriteria | None = None


class ScoreCVResponse(BaseModel):
    score: float
    reasoning: str


class ScoreUploadedCVResponse(BaseModel):
    job_id: int
    score: float
    reasoning: str
    min_score: float
    passed: bool
    candidate_email: str | None = None


class RankCandidatesRequest(BaseModel):
    job_id: int
    min_score: float = Field(default=60.0, ge=0.0, le=100.0)
    notify_candidates: bool = False
    criteria: HRScoreCriteria | None = None


class RankedCandidateResponse(BaseModel):
    application_id: int
    candidate_id: int
    candidate_name: str
    candidate_email: str
    score: float
    passed: bool
    reasoning: str


class RankCandidatesResult(BaseModel):
    total_scored: int
    total_passed: int
    min_score: float
    items: list[RankedCandidateResponse]


class NotifyScreeningResultRequest(BaseModel):
    application_id: int
    min_score: float = Field(default=60.0, ge=0.0, le=100.0)


class NotifyScreeningResultResponse(BaseModel):
    application_id: int
    candidate_email: str
    job_title: str
    score: float
    min_score: float
    passed: bool


class RankCandidatesAsyncRequest(BaseModel):
    job_id: int
    min_score: float = Field(default=60.0, ge=0.0, le=100.0)
    notify_candidates: bool = False
    criteria: HRScoreCriteria | None = None


class RankCandidatesAsyncSubmitResponse(BaseModel):
    scoring_job_id: str
    status: str
    total_items: int
    submitted_items: int
    failed_items: int
    queued_items: int


class RankCandidatesAsyncItemResponse(BaseModel):
    request_id: str
    application_id: int
    candidate_id: int | None = None
    candidate_name: str | None = None
    candidate_email: str | None = None
    status: str
    score: float | None = None
    passed: bool | None = None
    reasoning: str | None = None
    provider: str | None = None
    error: str | None = None
    processed_at: datetime | None = None


class RankCandidatesAsyncStatusResponse(BaseModel):
    scoring_job_id: str
    status: str
    job_id: int
    min_score: float
    notify_candidates: bool
    total_items: int
    submitted_items: int
    processed_items: int
    failed_items: int
    pending_items: int
    items: list[RankCandidatesAsyncItemResponse]
