import asyncio
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def _create_interview_event_sync(
    candidate_email: str,
    starts_at: datetime,
    ends_at: datetime,
    summary: str,
    description: str | None = None,
    location: str | None = None,
    create_meet_link: bool = False,
) -> dict[str, str | None]:
    service = _get_calendar_service()

    desc = description or ""
    if candidate_email:
        desc = f"Candidate: {candidate_email}\n{desc}"

    event_body = {
        "summary": summary,
        "description": desc,
        "location": location or "",
        "start": {
            "dateTime": starts_at.isoformat(),
            "timeZone": "Asia/Ho_Chi_Minh",
        },
        "end": {
            "dateTime": ends_at.isoformat(),
            "timeZone": "Asia/Ho_Chi_Minh",
        },
    }

    event = (
        service.events()
        .insert(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            body=event_body,
        )
        .execute()
    )

    return {
        "event_id": event.get("id"),
        "calendar_url": event.get("htmlLink"),
        "meeting_link": None,
    }


async def create_interview_event(
    candidate_email: str,
    starts_at: datetime,
    ends_at: datetime,
    summary: str,
    description: str | None = None,
    location: str | None = None,
    create_meet_link: bool = False,
) -> dict[str, str | None]:
    return await asyncio.to_thread(
        _create_interview_event_sync,
        candidate_email, starts_at, ends_at, summary,
        description, location, create_meet_link,
    )


def _update_interview_event_sync(
    event_id: str,
    candidate_email: str,
    starts_at: datetime,
    ends_at: datetime,
    summary: str,
    description: str | None = None,
    location: str | None = None,
    create_meet_link: bool = False,
) -> dict[str, str | None]:
    service = _get_calendar_service()

    desc = description or ""
    if candidate_email:
        desc = f"Candidate: {candidate_email}\n{desc}"

    event_body = {
        "summary": summary,
        "description": desc,
        "location": location or "",
        "start": {
            "dateTime": starts_at.isoformat(),
            "timeZone": "Asia/Ho_Chi_Minh",
        },
        "end": {
            "dateTime": ends_at.isoformat(),
            "timeZone": "Asia/Ho_Chi_Minh",
        },
    }

    event = (
        service.events()
        .update(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            eventId=event_id,
            body=event_body,
        )
        .execute()
    )

    return {
        "event_id": event.get("id"),
        "calendar_url": event.get("htmlLink"),
        "meeting_link": None,
    }


async def update_interview_event(
    event_id: str,
    candidate_email: str,
    starts_at: datetime,
    ends_at: datetime,
    summary: str,
    description: str | None = None,
    location: str | None = None,
    create_meet_link: bool = False,
) -> dict[str, str | None]:
    return await asyncio.to_thread(
        _update_interview_event_sync,
        event_id, candidate_email, starts_at, ends_at, summary,
        description, location, create_meet_link,
    )


def _delete_interview_event_sync(event_id: str | None) -> None:
    if not event_id:
        return

    service = _get_calendar_service()
    service.events().delete(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        eventId=event_id,
    ).execute()


async def delete_interview_event(event_id: str | None) -> None:
    await asyncio.to_thread(_delete_interview_event_sync, event_id)