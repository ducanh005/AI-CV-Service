from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import logging

from app.core.exceptions import AppException

from app.integrations.google_calendar_integration import (
    create_interview_event,
    delete_interview_event,
    update_interview_event,
)
from app.models import Interview, Application, User
from app.schemas.interview import InterviewCreateRequest, InterviewUpdateRequest
from app.models.enums import InterviewMode
from app.models.job import Job

logger = logging.getLogger(__name__)



class InterviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_application_with_relations(self, application_id: int) -> Application:
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(
                selectinload(Application.candidate),
                selectinload(Application.job).selectinload(Job.company),
            )
        )
        result = await self.db.execute(stmt)
        application = result.scalar_one_or_none()
        if not application:
            raise AppException("Application not found", status_code=404)
        return application

    async def _get_interview(self, interview_id: int) -> Interview:
        stmt = (
            select(Interview)
            .where(Interview.id == interview_id)
            .options(
                selectinload(Interview.application)
                .selectinload(Application.job)
                .selectinload(Job.company),
                selectinload(Interview.candidate),
            )
        )
        result = await self.db.execute(stmt)
        interview = result.scalar_one_or_none()
        if not interview:
            raise AppException("Interview not found", status_code=404)
        return interview

    @staticmethod
    def serialize(interview: Interview) -> dict:
        application = getattr(interview, "application", None)
        candidate = getattr(interview, "candidate", None)
        job = getattr(application, "job", None) if application else None
        company = getattr(job, "company", None) if job else None

        return {
            "id": interview.id,
            "application_id": interview.application_id,
            "candidate_id": interview.candidate_id,
            "hr_id": interview.hr_id,
            "title": interview.title,
            "starts_at": interview.starts_at,
            "ends_at": interview.ends_at,
            "interview_mode": interview.interview_mode,
            "location": interview.location,
            "notes": interview.notes,
            "result_status": interview.result_status,
            "calendar_event_id": interview.calendar_event_id,
            "calendar_url": interview.calendar_url,
            "meeting_link": interview.meeting_link,
            "candidate_name": candidate.full_name if candidate else None,
            "candidate_email": candidate.email if candidate else None,
            "job_title": job.title if job else None,
            "company_name": company.name if company else None,
            "created_at": interview.created_at,
            "updated_at": interview.updated_at,
        }

    async def list_interviews_for_hr(self, hr_user: User) -> list[Interview]:
        stmt = (
            select(Interview)
            .where(Interview.hr_id == hr_user.id)
            .order_by(Interview.starts_at.desc())
            .options(
                selectinload(Interview.application)
                .selectinload(Application.job)
                .selectinload(Job.company),
                selectinload(Interview.candidate),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def schedule_interview(
        self,
        payload: InterviewCreateRequest,
        hr_user: User,
    ) -> Interview:
        logger.info(f"[INTERVIEW] Starting creation: app_id={payload.application_id}, title={payload.title}")
        try:
            application = await self._get_application_with_relations(payload.application_id)
            candidate = application.candidate
            logger.info(f"[INTERVIEW] Found candidate: {candidate.email}")

            # Store interview_mode as string value
            interview_mode_value = payload.interview_mode.value if hasattr(payload.interview_mode, 'value') else str(payload.interview_mode)
            result_status_value = "scheduled"

            interview = Interview(
                application_id=application.id,
                candidate_id=candidate.id,
                hr_id=hr_user.id,
                title=payload.title,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                interview_mode=interview_mode_value,
                location=payload.location,
                notes=payload.notes,
                result_status=result_status_value,
            )

            self.db.add(interview)
            await self.db.commit()
            await self.db.refresh(interview)
            logger.info(f"[INTERVIEW] Saved locally: id={interview.id}, mode={interview_mode_value}")

            try:
                event = await create_interview_event(
                    candidate_email=candidate.email,
                    starts_at=payload.starts_at,
                    ends_at=payload.ends_at,
                    summary=payload.title,
                    description=payload.notes,
                    location=payload.location,
                    create_meet_link=interview_mode_value == "online",
                )
                interview.calendar_event_id = event["event_id"]
                interview.calendar_url = event["calendar_url"]
                interview.meeting_link = event["meeting_link"]
                await self.db.commit()
                await self.db.refresh(interview)
                logger.info(f"[INTERVIEW] Google Calendar synced: {interview.id}")
            except Exception as exc:
                logger.warning(
                    f"[INTERVIEW] Google Calendar sync deferred for {interview.id}: {exc}",
                )

            result = await self._get_interview(interview.id)
            logger.info(f"[INTERVIEW] Successfully created: id={result.id}")
            return result
        except Exception as exc:
            logger.error(f"[INTERVIEW] Error creating interview: {exc}", exc_info=True)
            raise

    async def sync_interview_to_google(self, interview_id: int) -> Interview:
        interview = await self._get_interview(interview_id)
        candidate_email = interview.candidate.email

        if interview.calendar_event_id:
            event = await update_interview_event(
                event_id=interview.calendar_event_id,
                candidate_email=candidate_email,
                starts_at=interview.starts_at,
                ends_at=interview.ends_at,
                summary=interview.title,
                description=interview.notes,
                location=interview.location,
                create_meet_link=interview.interview_mode == "online",
            )
        else:
            event = await create_interview_event(
                candidate_email=candidate_email,
                starts_at=interview.starts_at,
                ends_at=interview.ends_at,
                summary=interview.title,
                description=interview.notes,
                location=interview.location,
                create_meet_link=interview.interview_mode == "online",
            )

        interview.calendar_event_id = event["event_id"]
        interview.calendar_url = event["calendar_url"]
        interview.meeting_link = event["meeting_link"]
        await self.db.commit()
        return await self._get_interview(interview.id)

    async def update_interview(
        self,
        interview_id: int,
        payload: InterviewUpdateRequest,
        hr_user: User,
    ) -> Interview:
        interview = await self._get_interview(interview_id)

        if interview.hr_id != hr_user.id:
            raise AppException("You do not have permission to update this interview", status_code=403)

        starts_at = payload.starts_at or interview.starts_at
        ends_at = payload.ends_at or interview.ends_at
        if ends_at <= starts_at:
            raise AppException("ends_at must be greater than starts_at", status_code=400)

        if payload.title is not None:
            interview.title = payload.title
        if payload.starts_at is not None:
            interview.starts_at = payload.starts_at
        if payload.ends_at is not None:
            interview.ends_at = payload.ends_at
        if payload.interview_mode is not None:
            interview_mode_value = payload.interview_mode.value if hasattr(payload.interview_mode, 'value') else str(payload.interview_mode)
            interview.interview_mode = interview_mode_value
        if payload.notes is not None:
            interview.notes = payload.notes
        if payload.location is not None:
            interview.location = payload.location
        if payload.result_status is not None:
            result_status_value = payload.result_status.value if hasattr(payload.result_status, 'value') else str(payload.result_status)
            interview.result_status = result_status_value

        if interview.interview_mode == "offline" and not interview.location:
            raise AppException("location is required for offline interviews", status_code=400)

        candidate = interview.candidate
        try:
            if interview.calendar_event_id:
                event = await update_interview_event(
                    event_id=interview.calendar_event_id,
                    candidate_email=candidate.email,
                    starts_at=interview.starts_at,
                    ends_at=interview.ends_at,
                    summary=interview.title,
                    description=interview.notes,
                    location=interview.location,
                    create_meet_link=interview.interview_mode == "online",
                )
            else:
                event = await create_interview_event(
                    candidate_email=candidate.email,
                    starts_at=interview.starts_at,
                    ends_at=interview.ends_at,
                    summary=interview.title,
                    description=interview.notes,
                    location=interview.location,
                    create_meet_link=interview.interview_mode == "online",
                )
            interview.calendar_event_id = event["event_id"]
            interview.calendar_url = event["calendar_url"]
            interview.meeting_link = event["meeting_link"]
        except Exception as exc:
            logger.warning(
                f"[INTERVIEW] Google Calendar event update failed: {exc}",
            )

        await self.db.commit()
        return await self._get_interview(interview.id)

    async def delete_interview(self, interview_id: int, hr_user: User) -> None:
        interview = await self._get_interview(interview_id)

        if interview.hr_id != hr_user.id:
            raise AppException("You do not have permission to delete this interview", status_code=403)

        await delete_interview_event(interview.calendar_event_id)
        await self.db.delete(interview)
        await self.db.commit()
