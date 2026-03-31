from datetime import datetime

from pydantic import BaseModel, Field


class InterviewCreateRequest(BaseModel):
    application_id: int
    starts_at: datetime
    ends_at: datetime
    notes: str | None = Field(default=None, max_length=2000)


class InterviewResponse(BaseModel):
    id: int
    application_id: int
    candidate_id: int
    hr_id: int | None
    starts_at: datetime
    ends_at: datetime
    calendar_event_id: str | None
    meeting_link: str | None
    notes: str | None
