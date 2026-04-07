from datetime import datetime

from pydantic import BaseModel, Field, model_validator, ConfigDict

from app.models.enums import InterviewMode, InterviewResultStatus


class InterviewCreateRequest(BaseModel):
    application_id: int
    title: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    ends_at: datetime
    interview_mode: InterviewMode = InterviewMode.ONLINE
    location: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    
    @model_validator(mode="after")
    def validate_time_range(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be greater than starts_at")
        if self.interview_mode == InterviewMode.OFFLINE and not self.location:
            raise ValueError("location is required for offline interviews")
        return self

class InterviewUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    interview_mode: InterviewMode | None = None
    location: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    result_status: InterviewResultStatus | None = None

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be greater than starts_at")
        return self
class InterviewResponse(BaseModel):
    id: int
    application_id: int
    candidate_id: int
    hr_id: int | None
    
    title: str
    starts_at: datetime
    ends_at: datetime
    interview_mode: str
    location: str | None
    notes: str | None
    result_status: str
    
    calendar_url: str | None
    calendar_event_id: str | None
    meeting_link: str | None
    
    candidate_name: str | None = None
    candidate_email: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)