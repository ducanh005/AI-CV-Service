from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.employee import Employee
from app.models.enums import ContractType, OnboardingStatus, TaskPriority
from app.models.onboarding import (
    OnboardingAssignment,
    OnboardingTask,
    OnboardingTaskProgress,
    OnboardingTemplate,
)


class OnboardingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Templates ─────────────────────────────────────

    async def create_template(
        self,
        company_id: int,
        name: str,
        description: str | None,
        tasks: list[dict],
    ) -> OnboardingTemplate:
        existing = await self.db.scalar(
            select(OnboardingTemplate).where(
                OnboardingTemplate.name == name,
                OnboardingTemplate.company_id == company_id,
                OnboardingTemplate.deleted_at.is_(None),
            )
        )
        if existing:
            raise AppException("Template name already exists", status_code=400)

        template = OnboardingTemplate(
            name=name,
            description=description,
            company_id=company_id,
        )
        for t in tasks:
            template.tasks.append(
                OnboardingTask(
                    title=t["title"],
                    description=t.get("description"),
                    priority=t.get("priority", TaskPriority.MEDIUM.value),
                    order=t.get("order", 0),
                )
            )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template, ["tasks"])
        return template

    async def list_templates(self, company_id: int) -> list[dict]:
        stmt = (
            select(OnboardingTemplate)
            .options(selectinload(OnboardingTemplate.tasks))
            .where(
                OnboardingTemplate.company_id == company_id,
                OnboardingTemplate.deleted_at.is_(None),
            )
            .order_by(OnboardingTemplate.created_at.desc())
        )
        templates = (await self.db.scalars(stmt)).all()
        return [self._template_to_dict(t) for t in templates]

    async def get_template(self, template_id: int, company_id: int) -> OnboardingTemplate:
        tmpl = await self.db.scalar(
            select(OnboardingTemplate)
            .options(selectinload(OnboardingTemplate.tasks))
            .where(
                OnboardingTemplate.id == template_id,
                OnboardingTemplate.company_id == company_id,
                OnboardingTemplate.deleted_at.is_(None),
            )
        )
        if not tmpl:
            raise AppException("Template not found", status_code=404)
        return tmpl

    async def update_template(
        self,
        tmpl: OnboardingTemplate,
        name: str | None,
        description: str | None,
        tasks: list[dict] | None,
    ) -> OnboardingTemplate:
        if name is not None:
            existing = await self.db.scalar(
                select(OnboardingTemplate).where(
                    OnboardingTemplate.name == name,
                    OnboardingTemplate.company_id == tmpl.company_id,
                    OnboardingTemplate.id != tmpl.id,
                    OnboardingTemplate.deleted_at.is_(None),
                )
            )
            if existing:
                raise AppException("Template name already exists", status_code=400)
            tmpl.name = name
        if description is not None:
            tmpl.description = description
        if tasks is not None:
            # Replace all tasks
            tmpl.tasks.clear()
            await self.db.flush()
            for t in tasks:
                tmpl.tasks.append(
                    OnboardingTask(
                        title=t["title"],
                        description=t.get("description"),
                        priority=t.get("priority", TaskPriority.MEDIUM.value),
                        order=t.get("order", 0),
                    )
                )
        await self.db.commit()
        await self.db.refresh(tmpl, ["tasks"])
        return tmpl

    async def delete_template(self, tmpl: OnboardingTemplate) -> None:
        # Check if assigned
        count = await self.db.scalar(
            select(func.count()).select_from(OnboardingAssignment).where(
                OnboardingAssignment.template_id == tmpl.id,
                OnboardingAssignment.status != OnboardingStatus.COMPLETED.value,
            )
        )
        if count and count > 0:
            raise AppException("Cannot delete template with active assignments", status_code=400)
        tmpl.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    def _template_to_dict(self, tmpl: OnboardingTemplate) -> dict:
        return {
            "id": tmpl.id,
            "name": tmpl.name,
            "description": tmpl.description,
            "company_id": tmpl.company_id,
            "task_count": len(tmpl.tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "priority": t.priority,
                    "order": t.order,
                }
                for t in tmpl.tasks
            ],
            "created_at": tmpl.created_at,
        }

    # ── Assignments ───────────────────────────────────

    async def create_assignment(
        self,
        company_id: int,
        employee_id: int,
        template_id: int,
        assigned_by_id: int,
        due_date=None,
        notes: str | None = None,
    ) -> OnboardingAssignment:
        # Validate employee — only probation employees
        emp = await self.db.scalar(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.company_id == company_id,
                Employee.deleted_at.is_(None),
            )
        )
        if not emp:
            raise AppException("Employee not found", status_code=404)
        if emp.contract_type != ContractType.PROBATION.value:
            raise AppException("Chỉ nhân viên thử việc mới được giao onboarding", status_code=400)

        # Validate template
        tmpl = await self.db.scalar(
            select(OnboardingTemplate)
            .options(selectinload(OnboardingTemplate.tasks))
            .where(
                OnboardingTemplate.id == template_id,
                OnboardingTemplate.company_id == company_id,
                OnboardingTemplate.deleted_at.is_(None),
            )
        )
        if not tmpl:
            raise AppException("Template not found", status_code=404)

        # Check duplicates
        existing = await self.db.scalar(
            select(OnboardingAssignment).where(
                OnboardingAssignment.employee_id == employee_id,
                OnboardingAssignment.template_id == template_id,
                OnboardingAssignment.status != OnboardingStatus.COMPLETED.value,
            )
        )
        if existing:
            raise AppException("Employee already has an active assignment for this template", status_code=400)

        assignment = OnboardingAssignment(
            status=OnboardingStatus.NOT_STARTED.value,
            due_date=due_date,
            notes=notes,
            employee_id=employee_id,
            template_id=template_id,
            assigned_by_id=assigned_by_id,
            company_id=company_id,
        )
        self.db.add(assignment)
        await self.db.flush()

        # Create progress items for each task
        for task in tmpl.tasks:
            self.db.add(
                OnboardingTaskProgress(
                    assignment_id=assignment.id,
                    task_id=task.id,
                    is_completed=False,
                )
            )

        await self.db.commit()
        return await self._load_assignment(assignment.id)

    async def list_assignments(
        self,
        company_id: int,
        employee_id: int | None = None,
        status: OnboardingStatus | None = None,
    ) -> list[dict]:
        stmt = (
            select(OnboardingAssignment)
            .options(
                selectinload(OnboardingAssignment.employee).selectinload(Employee.user),
                selectinload(OnboardingAssignment.employee).selectinload(Employee.department),
                selectinload(OnboardingAssignment.template),
                selectinload(OnboardingAssignment.assigned_by),
                selectinload(OnboardingAssignment.task_progress).selectinload(OnboardingTaskProgress.task),
            )
            .where(OnboardingAssignment.company_id == company_id)
            .order_by(OnboardingAssignment.created_at.desc())
        )
        if employee_id:
            stmt = stmt.where(OnboardingAssignment.employee_id == employee_id)
        if status:
            stmt = stmt.where(OnboardingAssignment.status == status.value)

        assignments = (await self.db.scalars(stmt)).all()
        return [self._assignment_to_dict(a) for a in assignments]

    async def get_assignment(self, assignment_id: int, company_id: int) -> OnboardingAssignment:
        a = await self._load_assignment(assignment_id)
        if not a or a.company_id != company_id:
            raise AppException("Assignment not found", status_code=404)
        return a

    async def update_assignment(
        self, assignment: OnboardingAssignment, due_date=None, notes: str | None = None,
    ) -> OnboardingAssignment:
        if due_date is not None:
            assignment.due_date = due_date
        if notes is not None:
            assignment.notes = notes
        await self.db.commit()
        return await self._load_assignment(assignment.id)

    async def delete_assignment(self, assignment: OnboardingAssignment) -> None:
        await self.db.delete(assignment)
        await self.db.commit()

    async def toggle_task(
        self, assignment_id: int, task_id: int, company_id: int, note: str | None = None,
    ) -> OnboardingAssignment:
        assignment = await self.get_assignment(assignment_id, company_id)

        progress = None
        for tp in assignment.task_progress:
            if tp.task_id == task_id:
                progress = tp
                break
        if not progress:
            raise AppException("Task not found in this assignment", status_code=404)

        progress.is_completed = not progress.is_completed
        progress.completed_at = datetime.now(timezone.utc) if progress.is_completed else None
        if note is not None:
            progress.note = note

        # Recalculate assignment status
        total = len(assignment.task_progress)
        done = sum(1 for tp in assignment.task_progress if tp.is_completed)
        if done == 0:
            assignment.status = OnboardingStatus.NOT_STARTED.value
            assignment.completed_at = None
        elif done == total:
            assignment.status = OnboardingStatus.COMPLETED.value
            assignment.completed_at = datetime.now(timezone.utc)
            # Auto-convert probation → permanent
            emp = await self.db.scalar(
                select(Employee).where(Employee.id == assignment.employee_id)
            )
            if emp and emp.contract_type == ContractType.PROBATION.value:
                emp.contract_type = ContractType.PERMANENT.value
        else:
            assignment.status = OnboardingStatus.IN_PROGRESS.value
            assignment.completed_at = None

        await self.db.commit()
        return await self._load_assignment(assignment.id)

    async def _load_assignment(self, assignment_id: int) -> OnboardingAssignment | None:
        return await self.db.scalar(
            select(OnboardingAssignment)
            .options(
                selectinload(OnboardingAssignment.employee).selectinload(Employee.user),
                selectinload(OnboardingAssignment.employee).selectinload(Employee.department),
                selectinload(OnboardingAssignment.template),
                selectinload(OnboardingAssignment.assigned_by),
                selectinload(OnboardingAssignment.task_progress).selectinload(OnboardingTaskProgress.task),
            )
            .where(OnboardingAssignment.id == assignment_id)
        )

    def _assignment_to_dict(self, a: OnboardingAssignment) -> dict:
        progress_list = sorted(a.task_progress, key=lambda tp: tp.task.order if tp.task else 0)
        total = len(progress_list)
        done = sum(1 for tp in progress_list if tp.is_completed)
        return {
            "id": a.id,
            "status": a.status,
            "due_date": a.due_date,
            "completed_at": a.completed_at,
            "notes": a.notes,
            "employee_id": a.employee_id,
            "employee_name": a.employee.user.full_name if a.employee and a.employee.user else None,
            "employee_code": a.employee.employee_code if a.employee else None,
            "employee_position": a.employee.position if a.employee else None,
            "employee_department": a.employee.department.name if a.employee and a.employee.department else None,
            "employee_contract_type": a.employee.contract_type if a.employee else None,
            "template_id": a.template_id,
            "template_name": a.template.name if a.template else None,
            "assigned_by_name": a.assigned_by.full_name if a.assigned_by else None,
            "company_id": a.company_id,
            "total_tasks": total,
            "completed_tasks": done,
            "task_progress": [
                {
                    "id": tp.id,
                    "task_id": tp.task_id,
                    "task_title": tp.task.title if tp.task else "",
                    "task_description": tp.task.description if tp.task else None,
                    "task_priority": tp.task.priority if tp.task else "medium",
                    "task_order": tp.task.order if tp.task else 0,
                    "is_completed": tp.is_completed,
                    "completed_at": tp.completed_at,
                    "note": tp.note,
                }
                for tp in progress_list
            ],
            "created_at": a.created_at,
        }
