from datetime import date, datetime, time, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.enums import AttendanceStatus


class AttendanceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        company_id: int,
        employee_id: int,
        att_date: date,
        check_in: time | None,
        check_out: time | None,
        status: AttendanceStatus,
        notes: str | None,
    ) -> Attendance:
        # Validate employee
        emp = await self.db.scalar(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.company_id == company_id,
                Employee.deleted_at.is_(None),
            )
        )
        if not emp:
            raise AppException("Employee not found", status_code=404)

        # Check duplicate
        existing = await self.db.scalar(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.date == att_date,
            )
        )
        if existing:
            raise AppException("Attendance record already exists for this date", status_code=400)

        work_hours = self._calc_hours(check_in, check_out)

        att = Attendance(
            date=att_date,
            check_in=check_in,
            check_out=check_out,
            status=status.value,
            work_hours=work_hours,
            notes=notes,
            employee_id=employee_id,
            company_id=company_id,
        )
        self.db.add(att)
        await self.db.commit()
        await self.db.refresh(att)
        return await self._load(att.id)

    async def list(
        self,
        company_id: int,
        employee_id: int | None = None,
        status: AttendanceStatus | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict]:
        stmt = (
            select(Attendance)
            .options(
                selectinload(Attendance.employee).selectinload(Employee.user),
                selectinload(Attendance.employee).selectinload(Employee.department),
            )
            .where(Attendance.company_id == company_id)
            .order_by(Attendance.date.desc(), Attendance.created_at.desc())
        )
        if employee_id:
            stmt = stmt.where(Attendance.employee_id == employee_id)
        if status:
            stmt = stmt.where(Attendance.status == status.value)
        if from_date:
            stmt = stmt.where(Attendance.date >= from_date)
        if to_date:
            stmt = stmt.where(Attendance.date <= to_date)

        rows = (await self.db.scalars(stmt)).all()
        return [self._to_dict(r) for r in rows]

    async def get(self, att_id: int, company_id: int) -> Attendance:
        att = await self._load(att_id)
        if not att or att.company_id != company_id:
            raise AppException("Attendance record not found", status_code=404)
        return att

    async def update(
        self,
        att: Attendance,
        check_in: time | None = None,
        check_out: time | None = None,
        status: AttendanceStatus | None = None,
        notes: str | None = None,
    ) -> Attendance:
        if check_in is not None:
            att.check_in = check_in
        if check_out is not None:
            att.check_out = check_out
        if status is not None:
            att.status = status.value
        if notes is not None:
            att.notes = notes
        att.work_hours = self._calc_hours(att.check_in, att.check_out)
        await self.db.commit()
        return await self._load(att.id)

    async def delete(self, att: Attendance) -> None:
        await self.db.delete(att)
        await self.db.commit()

    async def _load(self, att_id: int) -> Attendance | None:
        return await self.db.scalar(
            select(Attendance)
            .options(
                selectinload(Attendance.employee).selectinload(Employee.user),
                selectinload(Attendance.employee).selectinload(Employee.department),
            )
            .where(Attendance.id == att_id)
        )

    def _to_dict(self, att: Attendance) -> dict:
        emp = att.employee
        return {
            "id": att.id,
            "date": att.date,
            "check_in": att.check_in,
            "check_out": att.check_out,
            "status": att.status,
            "work_hours": att.work_hours,
            "notes": att.notes,
            "employee_id": att.employee_id,
            "employee_name": emp.user.full_name if emp and emp.user else None,
            "employee_code": emp.employee_code if emp else None,
            "department_name": emp.department.name if emp and emp.department else None,
            "company_id": att.company_id,
            "created_at": att.created_at,
        }

    @staticmethod
    def _calc_hours(ci: time | None, co: time | None) -> float | None:
        if ci and co:
            dt_in = datetime.combine(date.today(), ci)
            dt_out = datetime.combine(date.today(), co)
            diff = (dt_out - dt_in).total_seconds() / 3600
            return round(max(diff, 0), 2)
        return None
