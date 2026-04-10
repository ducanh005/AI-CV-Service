from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db_session
from app.models import User
from app.models.enums import UserRole
from app.schemas.interview import (
    InterviewCreateRequest,
    InterviewResponse,
    InterviewUpdateRequest,
)
from app.services.interview_service import InterviewService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=list[InterviewResponse])
async def list_interviews(
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> list[InterviewResponse]:
    service = InterviewService(db)
    interviews = await service.list_interviews_for_hr(current_user)
    return [InterviewResponse(**service.serialize(item)) for item in interviews]


@router.post("", response_model=InterviewResponse)
async def create_interview(
    payload: InterviewCreateRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> InterviewResponse:
    service = InterviewService(db)
    interview = await service.schedule_interview(payload=payload, hr_user=current_user)

    if interview.meeting_link:
        NotificationService.send_interview_invitation(
            interview.candidate.email,
            interview.meeting_link,
        )
    elif interview.calendar_url:
        NotificationService.send_interview_invitation(
            interview.candidate.email,
            interview.calendar_url,
        )

    return InterviewResponse(**service.serialize(interview))


@router.post("/{interview_id}/sync", response_model=InterviewResponse)
async def sync_interview(
    interview_id: int,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> InterviewResponse:
    service = InterviewService(db)
    interview = await service.sync_interview_to_google(interview_id)
    return InterviewResponse(**service.serialize(interview))


@router.patch("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: int,
    payload: InterviewUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> InterviewResponse:
    service = InterviewService(db)
    interview = await service.update_interview(
        interview_id=interview_id,
        payload=payload,
        hr_user=current_user,
    )
    return InterviewResponse(**service.serialize(interview))


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: int,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    service = InterviewService(db)
    await service.delete_interview(interview_id=interview_id, hr_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)