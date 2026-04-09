from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.department import Department
from app.models.employee import Employee


class DepartmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_department(self, company_id: int, name: str, description: str | None, manager_id: int | None) -> Department:
        existing = await self.db.scalar(
            select(Department).where(
                Department.name == name,
                Department.company_id == company_id,
                Department.deleted_at.is_(None),
            )
        )
        if existing:
            raise AppException("Department already exists in this company", status_code=400)

        dept = Department(name=name, description=description, company_id=company_id, manager_id=manager_id)
        self.db.add(dept)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def list_departments(self, company_id: int) -> list[dict]:
        stmt = (
            select(
                Department,
                func.count(Employee.id).label("employee_count"),
            )
            .outerjoin(Employee, (Employee.department_id == Department.id) & Employee.deleted_at.is_(None))
            .where(Department.company_id == company_id, Department.deleted_at.is_(None))
            .group_by(Department.id)
            .order_by(Department.name)
            .options(selectinload(Department.manager))
        )
        rows = (await self.db.execute(stmt)).all()
        results = []
        for dept, emp_count in rows:
            results.append({
                "id": dept.id,
                "name": dept.name,
                "description": dept.description,
                "company_id": dept.company_id,
                "manager_id": dept.manager_id,
                "manager_name": dept.manager.full_name if dept.manager else None,
                "employee_count": emp_count,
            })
        return results

    async def get_department(self, department_id: int, company_id: int) -> Department:
        dept = await self.db.scalar(
            select(Department).where(
                Department.id == department_id,
                Department.company_id == company_id,
                Department.deleted_at.is_(None),
            )
        )
        if not dept:
            raise AppException("Department not found", status_code=404)
        return dept

    async def update_department(self, dept: Department, name: str | None, description: str | None, manager_id: int | None) -> Department:
        if name is not None:
            existing = await self.db.scalar(
                select(Department).where(
                    Department.name == name,
                    Department.company_id == dept.company_id,
                    Department.id != dept.id,
                    Department.deleted_at.is_(None),
                )
            )
            if existing:
                raise AppException("Department name already exists", status_code=400)
            dept.name = name
        if description is not None:
            dept.description = description
        if manager_id is not None:
            dept.manager_id = manager_id
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def delete_department(self, dept: Department) -> None:
        emp_count = await self.db.scalar(
            select(func.count(Employee.id)).where(
                Employee.department_id == dept.id,
                Employee.deleted_at.is_(None),
            )
        )
        if emp_count and emp_count > 0:
            raise AppException("Cannot delete department with active employees", status_code=400)
        from datetime import datetime, timezone
        dept.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
