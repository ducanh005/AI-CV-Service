from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models.enums import AttendanceStatus, UserRole
from app.models.user import User
from app.schemas.attendance import AttendanceCreateRequest, AttendanceResponse, AttendanceUpdateRequest
from app.services.attendance_service import AttendanceService

router = APIRouter()


def _company_id(user: User) -> int:
    if not user.company_id:
        raise AppException("User is not associated with any company", status_code=400)
    return user.company_id


@router.post("", response_model=AttendanceResponse)
async def create_attendance(
    payload: AttendanceCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> AttendanceResponse:
    cid = _company_id(current_user)
    svc = AttendanceService(db)
    att = await svc.create(
        company_id=cid,
        employee_id=payload.employee_id,
        att_date=payload.date,
        check_in=payload.check_in,
        check_out=payload.check_out,
        status=payload.status,
        notes=payload.notes,
    )
    return AttendanceResponse(**svc._to_dict(att))


@router.get("", response_model=list[AttendanceResponse])
async def list_attendances(
    employee_id: int | None = Query(default=None),
    status: AttendanceStatus | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> list[AttendanceResponse]:
    cid = _company_id(current_user)
    rows = await AttendanceService(db).list(cid, employee_id, status, from_date, to_date)
    return [AttendanceResponse(**r) for r in rows]


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance(
    attendance_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> AttendanceResponse:
    cid = _company_id(current_user)
    svc = AttendanceService(db)
    att = await svc.get(attendance_id, cid)
    return AttendanceResponse(**svc._to_dict(att))


@router.patch("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: int,
    payload: AttendanceUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> AttendanceResponse:
    cid = _company_id(current_user)
    svc = AttendanceService(db)
    att = await svc.get(attendance_id, cid)
    updated = await svc.update(att, payload.check_in, payload.check_out, payload.status, payload.notes)
    return AttendanceResponse(**svc._to_dict(updated))


@router.delete("/{attendance_id}")
async def delete_attendance(
    attendance_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    cid = _company_id(current_user)
    svc = AttendanceService(db)
    att = await svc.get(attendance_id, cid)
    await svc.delete(att)
    return {"detail": "Attendance record deleted"}
