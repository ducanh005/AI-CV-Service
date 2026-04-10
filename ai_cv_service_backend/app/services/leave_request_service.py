from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.employee import Employee
from app.models.enums import LeaveStatus, LeaveType
from app.models.leave_request import LeaveRequest


class LeaveRequestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        company_id: int,
        employee_id: int,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        reason: str | None,
    ) -> LeaveRequest:
        emp = await self.db.scalar(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.company_id == company_id,
                Employee.deleted_at.is_(None),
            )
        )
        if not emp:
            raise AppException("Employee not found", status_code=404)

        total_days = (end_date - start_date).days + 1

        lr = LeaveRequest(
            leave_type=leave_type.value,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            status=LeaveStatus.PENDING.value,
            employee_id=employee_id,
            company_id=company_id,
        )
        self.db.add(lr)
        await self.db.commit()
        await self.db.refresh(lr)
        return await self._load(lr.id)

    async def list(
        self,
        company_id: int,
        employee_id: int | None = None,
        status: LeaveStatus | None = None,
        leave_type: LeaveType | None = None,
    ) -> list[dict]:
        stmt = (
            select(LeaveRequest)
            .options(
                selectinload(LeaveRequest.employee).selectinload(Employee.user),
                selectinload(LeaveRequest.employee).selectinload(Employee.department),
                selectinload(LeaveRequest.approved_by),
            )
            .where(LeaveRequest.company_id == company_id)
            .order_by(LeaveRequest.created_at.desc())
        )
        if employee_id:
            stmt = stmt.where(LeaveRequest.employee_id == employee_id)
        if status:
            stmt = stmt.where(LeaveRequest.status == status.value)
        if leave_type:
            stmt = stmt.where(LeaveRequest.leave_type == leave_type.value)

        rows = (await self.db.scalars(stmt)).all()
        return [self._to_dict(r) for r in rows]

    async def get(self, lr_id: int, company_id: int) -> LeaveRequest:
        lr = await self._load(lr_id)
        if not lr or lr.company_id != company_id:
            raise AppException("Leave request not found", status_code=404)
        return lr

    async def update(
        self,
        lr: LeaveRequest,
        leave_type: LeaveType | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        reason: str | None = None,
    ) -> LeaveRequest:
        if lr.status != LeaveStatus.PENDING.value:
            raise AppException("Can only edit pending requests", status_code=400)
        if leave_type is not None:
            lr.leave_type = leave_type.value
        if start_date is not None:
            lr.start_date = start_date
        if end_date is not None:
            lr.end_date = end_date
        if reason is not None:
            lr.reason = reason
        lr.total_days = (lr.end_date - lr.start_date).days + 1
        await self.db.commit()
        return await self._load(lr.id)

    async def approve(
        self,
        lr: LeaveRequest,
        new_status: LeaveStatus,
        approved_by_id: int,
        rejected_reason: str | None = None,
    ) -> LeaveRequest:
        if lr.status != LeaveStatus.PENDING.value:
            raise AppException("Request already processed", status_code=400)
        if new_status == LeaveStatus.PENDING:
            raise AppException("Invalid status", status_code=400)

        lr.status = new_status.value
        lr.approved_by_id = approved_by_id
        lr.approved_at = datetime.now(timezone.utc)
        if new_status == LeaveStatus.REJECTED and rejected_reason:
            lr.rejected_reason = rejected_reason
        await self.db.commit()
        return await self._load(lr.id)

    async def delete(self, lr: LeaveRequest) -> None:
        if lr.status != LeaveStatus.PENDING.value:
            raise AppException("Can only delete pending requests", status_code=400)
        await self.db.delete(lr)
        await self.db.commit()

    async def _load(self, lr_id: int) -> LeaveRequest | None:
        return await self.db.scalar(
            select(LeaveRequest)
            .options(
                selectinload(LeaveRequest.employee).selectinload(Employee.user),
                selectinload(LeaveRequest.employee).selectinload(Employee.department),
                selectinload(LeaveRequest.approved_by),
            )
            .where(LeaveRequest.id == lr_id)
        )

    def _to_dict(self, lr: LeaveRequest) -> dict:
        emp = lr.employee
        return {
            "id": lr.id,
            "leave_type": lr.leave_type,
            "start_date": lr.start_date,
            "end_date": lr.end_date,
            "total_days": lr.total_days,
            "reason": lr.reason,
            "status": lr.status,
            "rejected_reason": lr.rejected_reason,
            "approved_at": lr.approved_at,
            "approved_by_name": lr.approved_by.full_name if lr.approved_by else None,
            "employee_id": lr.employee_id,
            "employee_name": emp.user.full_name if emp and emp.user else None,
            "employee_code": emp.employee_code if emp else None,
            "department_name": emp.department.name if emp and emp.department else None,
            "company_id": lr.company_id,
            "created_at": lr.created_at,
        }
