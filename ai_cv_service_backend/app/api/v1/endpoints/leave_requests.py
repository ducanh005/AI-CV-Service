from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models.enums import LeaveStatus, LeaveType, UserRole
from app.models.user import User
from app.schemas.leave_request import (
    LeaveApproveRequest,
    LeaveCreateRequest,
    LeaveResponse,
    LeaveUpdateRequest,
)
from app.services.leave_request_service import LeaveRequestService

router = APIRouter()


def _company_id(user: User) -> int:
    if not user.company_id:
        raise AppException("User is not associated with any company", status_code=400)
    return user.company_id


@router.post("", response_model=LeaveResponse)
async def create_leave(
    payload: LeaveCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> LeaveResponse:
    cid = _company_id(current_user)
    svc = LeaveRequestService(db)
    lr = await svc.create(
        company_id=cid,
        employee_id=payload.employee_id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
    )
    return LeaveResponse(**svc._to_dict(lr))


@router.get("", response_model=list[LeaveResponse])
async def list_leaves(
    employee_id: int | None = Query(default=None),
    status: LeaveStatus | None = Query(default=None),
    leave_type: LeaveType | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> list[LeaveResponse]:
    cid = _company_id(current_user)
    rows = await LeaveRequestService(db).list(cid, employee_id, status, leave_type)
    return [LeaveResponse(**r) for r in rows]


@router.get("/{leave_id}", response_model=LeaveResponse)
async def get_leave(
    leave_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> LeaveResponse:
    cid = _company_id(current_user)
    svc = LeaveRequestService(db)
    lr = await svc.get(leave_id, cid)
    return LeaveResponse(**svc._to_dict(lr))


@router.patch("/{leave_id}", response_model=LeaveResponse)
async def update_leave(
    leave_id: int,
    payload: LeaveUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> LeaveResponse:
    cid = _company_id(current_user)
    svc = LeaveRequestService(db)
    lr = await svc.get(leave_id, cid)
    updated = await svc.update(lr, payload.leave_type, payload.start_date, payload.end_date, payload.reason)
    return LeaveResponse(**svc._to_dict(updated))


@router.post("/{leave_id}/approve", response_model=LeaveResponse)
async def approve_leave(
    leave_id: int,
    payload: LeaveApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> LeaveResponse:
    cid = _company_id(current_user)
    svc = LeaveRequestService(db)
    lr = await svc.get(leave_id, cid)
    updated = await svc.approve(lr, payload.status, current_user.id, payload.rejected_reason)
    return LeaveResponse(**svc._to_dict(updated))


@router.delete("/{leave_id}")
async def delete_leave(
    leave_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    cid = _company_id(current_user)
    svc = LeaveRequestService(db)
    lr = await svc.get(leave_id, cid)
    await svc.delete(lr)
    return {"detail": "Leave request deleted"}
