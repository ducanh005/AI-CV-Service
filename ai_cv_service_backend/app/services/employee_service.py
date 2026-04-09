from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.department import Department
from app.models.employee import Employee
from app.models.enums import ContractType, EmployeeStatus
from app.models.user import User


class EmployeeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_employee(
        self,
        company_id: int,
        user_id: int,
        department_id: int,
        employee_code: str,
        position: str,
        contract_type: ContractType,
        start_date: date,
        end_date: date | None,
        identity_number: str | None,
        notes: str | None,
    ) -> Employee:
        existing_code = await self.db.scalar(
            select(Employee).where(Employee.employee_code == employee_code, Employee.deleted_at.is_(None))
        )
        if existing_code:
            raise AppException("Employee code already exists", status_code=400)

        existing_user = await self.db.scalar(
            select(Employee).where(Employee.user_id == user_id, Employee.deleted_at.is_(None))
        )
        if existing_user:
            raise AppException("User already has an employee record", status_code=400)

        dept = await self.db.scalar(
            select(Department).where(
                Department.id == department_id,
                Department.company_id == company_id,
                Department.deleted_at.is_(None),
            )
        )
        if not dept:
            raise AppException("Department not found in this company", status_code=404)

        employee = Employee(
            employee_code=employee_code,
            position=position,
            status=EmployeeStatus.ACTIVE.value,
            contract_type=contract_type.value,
            start_date=start_date,
            end_date=end_date,
            identity_number=identity_number,
            notes=notes,
            user_id=user_id,
            department_id=department_id,
            company_id=company_id,
        )
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def list_employees(
        self,
        company_id: int,
        department_id: int | None = None,
        status: EmployeeStatus | None = None,
        search: str | None = None,
    ) -> list[dict]:
        stmt = (
            select(Employee)
            .options(selectinload(Employee.user), selectinload(Employee.department))
            .where(Employee.company_id == company_id, Employee.deleted_at.is_(None))
            .order_by(Employee.created_at.desc())
        )
        if department_id:
            stmt = stmt.where(Employee.department_id == department_id)
        if status:
            stmt = stmt.where(Employee.status == status.value)
        if search:
            stmt = stmt.join(User, Employee.user_id == User.id).where(
                User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
            )

        employees = (await self.db.scalars(stmt)).all()
        results = []
        for emp in employees:
            results.append({
                "id": emp.id,
                "employee_code": emp.employee_code,
                "position": emp.position,
                "status": emp.status,
                "contract_type": emp.contract_type,
                "start_date": emp.start_date,
                "end_date": emp.end_date,
                "identity_number": emp.identity_number,
                "notes": emp.notes,
                "user_id": emp.user_id,
                "department_id": emp.department_id,
                "company_id": emp.company_id,
                "full_name": emp.user.full_name if emp.user else None,
                "email": emp.user.email if emp.user else None,
                "phone": emp.user.phone if emp.user else None,
                "avatar_url": emp.user.avatar_url if emp.user else None,
                "department_name": emp.department.name if emp.department else None,
            })
        return results

    async def get_employee(self, employee_id: int, company_id: int) -> Employee:
        emp = await self.db.scalar(
            select(Employee)
            .options(selectinload(Employee.user), selectinload(Employee.department))
            .where(
                Employee.id == employee_id,
                Employee.company_id == company_id,
                Employee.deleted_at.is_(None),
            )
        )
        if not emp:
            raise AppException("Employee not found", status_code=404)
        return emp

    async def update_employee(
        self,
        emp: Employee,
        department_id: int | None,
        position: str | None,
        status: EmployeeStatus | None,
        contract_type: ContractType | None,
        start_date: date | None,
        end_date: date | None,
        identity_number: str | None,
        notes: str | None,
    ) -> Employee:
        if department_id is not None:
            dept = await self.db.scalar(
                select(Department).where(
                    Department.id == department_id,
                    Department.company_id == emp.company_id,
                    Department.deleted_at.is_(None),
                )
            )
            if not dept:
                raise AppException("Department not found in this company", status_code=404)
            emp.department_id = department_id
        if position is not None:
            emp.position = position
        if status is not None:
            emp.status = status.value
        if contract_type is not None:
            emp.contract_type = contract_type.value
        if start_date is not None:
            emp.start_date = start_date
        if end_date is not None:
            emp.end_date = end_date
        if identity_number is not None:
            emp.identity_number = identity_number
        if notes is not None:
            emp.notes = notes
        await self.db.commit()
        await self.db.refresh(emp, ["user", "department"])
        return emp

    async def delete_employee(self, emp: Employee) -> None:
        from datetime import datetime, timezone
        emp.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    def to_response(self, emp: Employee) -> dict:
        return {
            "id": emp.id,
            "employee_code": emp.employee_code,
            "position": emp.position,
            "status": emp.status,
            "contract_type": emp.contract_type,
            "start_date": emp.start_date,
            "end_date": emp.end_date,
            "identity_number": emp.identity_number,
            "notes": emp.notes,
            "user_id": emp.user_id,
            "department_id": emp.department_id,
            "company_id": emp.company_id,
            "full_name": emp.user.full_name if emp.user else None,
            "email": emp.user.email if emp.user else None,
            "phone": emp.user.phone if emp.user else None,
            "avatar_url": emp.user.avatar_url if emp.user else None,
            "department_name": emp.department.name if emp.department else None,
        }
