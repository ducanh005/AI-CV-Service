from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models import Application, User
from app.models.enums import UserRole
from app.schemas.interview import InterviewCreateRequest, InterviewResponse
from app.services.interview_service import InterviewService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("", response_model=InterviewResponse)
async def create_interview(
    payload: InterviewCreateRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> InterviewResponse:
    application = await db.get(Application, payload.application_id)
    if not application:
        raise AppException("Application not found", status_code=404)

    candidate = await db.get(User, application.candidate_id)
    if not candidate:
        raise AppException("Candidate not found", status_code=404)

    interview = await InterviewService(db).schedule_interview(
        application_id=application.id,
        candidate_id=candidate.id,
        hr_id=current_user.id,
        candidate_email=candidate.email,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        notes=payload.notes,
    )

    if interview.meeting_link:
        NotificationService.send_interview_invitation(candidate.email, interview.meeting_link)

    return InterviewResponse.model_validate(interview)
