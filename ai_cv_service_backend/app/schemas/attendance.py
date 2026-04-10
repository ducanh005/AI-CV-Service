from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.models.enums import AttendanceStatus


class AttendanceCreateRequest(BaseModel):
    employee_id: int
    date: date
    check_in: time | None = None
    check_out: time | None = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: str | None = None


class AttendanceUpdateRequest(BaseModel):
    check_in: time | None = None
    check_out: time | None = None
    status: AttendanceStatus | None = None
    notes: str | None = None


class AttendanceResponse(BaseModel):
    id: int
    date: date
    check_in: time | None = None
    check_out: time | None = None
    status: str
    work_hours: float | None = None
    notes: str | None = None
    employee_id: int
    employee_name: str | None = None
    employee_code: str | None = None
    department_name: str | None = None
    company_id: int
    created_at: datetime | None = None
