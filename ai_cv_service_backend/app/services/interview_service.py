from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.google_calendar_integration import create_interview_event
from app.models import Interview


class InterviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def schedule_interview(
        self,
        application_id: int,
        candidate_id: int,
        hr_id: int,
        candidate_email: str,
        starts_at,
        ends_at,
        notes: str | None,
    ) -> Interview:
        event = create_interview_event(
            candidate_email=candidate_email,
            starts_at=starts_at,
            ends_at=ends_at,
            summary="Interview Invitation",
        )
        interview = Interview(
            application_id=application_id,
            candidate_id=candidate_id,
            hr_id=hr_id,
            starts_at=starts_at,
            ends_at=ends_at,
            calendar_event_id=event["event_id"],
            meeting_link=event["meeting_link"],
            notes=notes,
        )
        self.db.add(interview)
        await self.db.commit()
        await self.db.refresh(interview)
        return interview
