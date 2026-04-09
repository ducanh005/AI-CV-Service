from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import LeaveStatus, LeaveType


class LeaveCreateRequest(BaseModel):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self


class LeaveUpdateRequest(BaseModel):
    leave_type: LeaveType | None = None
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = None


class LeaveApproveRequest(BaseModel):
    status: LeaveStatus
    rejected_reason: str | None = None


class LeaveResponse(BaseModel):
    id: int
    leave_type: str
    start_date: date
    end_date: date
    total_days: float
    reason: str | None = None
    status: str
    rejected_reason: str | None = None
    approved_at: datetime | None = None
    approved_by_name: str | None = None
    employee_id: int
    employee_name: str | None = None
    employee_code: str | None = None
    department_name: str | None = None
    company_id: int
    created_at: datetime | None = None
