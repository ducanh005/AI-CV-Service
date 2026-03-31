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
    reasoning: str


class RankCandidatesResult(BaseModel):
    total_scored: int
    total_passed: int
    min_score: float
    items: list[RankedCandidateResponse]
