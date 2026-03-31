from datetime import datetime
from uuid import uuid4


def create_interview_event(
    candidate_email: str,
    starts_at: datetime,
    ends_at: datetime,
    summary: str,
) -> dict[str, str]:
    # Mock return object. Replace with Google Calendar API call in production.
    event_id = f"mock-{uuid4().hex}"
    meeting_link = f"https://meet.google.com/{event_id[:3]}-{event_id[3:7]}-{event_id[7:11]}"
    return {
        "event_id": event_id,
        "meeting_link": meeting_link,
        "candidate_email": candidate_email,
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "summary": summary,
    }
