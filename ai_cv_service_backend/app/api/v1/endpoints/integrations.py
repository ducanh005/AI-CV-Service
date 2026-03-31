from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.integrations.gmail_integration import send_email_via_gmail
from app.integrations.google_calendar_integration import create_interview_event
from app.integrations.linkedin_integration import exchange_code_for_profile, get_linkedin_oauth_url
from app.models import User

router = APIRouter()


@router.get("/linkedin/oauth-url")
async def linkedin_oauth_url(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    state = f"user-{current_user.id}-{uuid4().hex}"
    return {"oauth_url": get_linkedin_oauth_url(state=state)}


@router.get("/linkedin/callback")
async def linkedin_callback(code: str = Query(..., min_length=4)) -> dict[str, str]:
    profile = exchange_code_for_profile(code)
    return {"message": "LinkedIn profile fetched", "email": profile["email"], "full_name": profile["full_name"]}


@router.get("/linkedin/import-candidate")
async def import_candidate_from_linkedin(code: str = Query(..., min_length=4)) -> dict:
    profile = exchange_code_for_profile(code)
    return {"imported": True, "profile": profile}


@router.post("/gmail/test-email")
async def send_test_email(
    to_email: str = Query(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    send_email_via_gmail(
        to_email=to_email,
        subject="AI CV Service Test Email",
        body=f"Hello from {current_user.full_name}, email integration is configured.",
    )
    return {"message": "Email task triggered"}


@router.post("/calendar/test-event")
async def create_test_calendar_event(
    candidate_email: str = Query(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    from datetime import datetime, timedelta, timezone

    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=1)
    event = create_interview_event(
        candidate_email=candidate_email,
        starts_at=starts_at,
        ends_at=ends_at,
        summary=f"Interview with {current_user.full_name}",
    )
    return {"event_id": event["event_id"], "meeting_link": event["meeting_link"]}
