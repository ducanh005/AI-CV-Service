from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models.enums import OnboardingStatus, UserRole
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingAssignmentCreateRequest,
    OnboardingAssignmentResponse,
    OnboardingAssignmentUpdateRequest,
    OnboardingTemplateCreateRequest,
    OnboardingTemplateResponse,
    OnboardingTemplateUpdateRequest,
    TaskToggleRequest,
)
from app.services.onboarding_service import OnboardingService

router = APIRouter()


def _company_id(user: User) -> int:
    if not user.company_id:
        raise AppException("User is not associated with any company", status_code=400)
    return user.company_id


# ── Templates ─────────────────────────────────────────

@router.post("/templates", response_model=OnboardingTemplateResponse)
async def create_template(
    payload: OnboardingTemplateCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> OnboardingTemplateResponse:
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    tmpl = await svc.create_template(
        company_id=cid,
        name=payload.name,
        description=payload.description,
        tasks=[t.model_dump() for t in payload.tasks],
    )
    return OnboardingTemplateResponse(**svc._template_to_dict(tmpl))


@router.get("/templates", response_model=list[OnboardingTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> list[OnboardingTemplateResponse]:
    cid = _company_id(current_user)
    rows = await OnboardingService(db).list_templates(cid)
    return [OnboardingTemplateResponse(**r) for r in rows]


@router.get("/templates/{template_id}", response_model=OnboardingTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> OnboardingTemplateResponse:
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    tmpl = await svc.get_template(template_id, cid)
    return OnboardingTemplateResponse(**svc._template_to_dict(tmpl))


@router.patch("/templates/{template_id}", response_model=OnboardingTemplateResponse)
async def update_template(
    template_id: int,
    payload: OnboardingTemplateUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> OnboardingTemplateResponse:
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    tmpl = await svc.get_template(template_id, cid)
    tasks_data = [t.model_dump() for t in payload.tasks] if payload.tasks is not None else None
    updated = await svc.update_template(tmpl, payload.name, payload.description, tasks_data)
    return OnboardingTemplateResponse(**svc._template_to_dict(updated))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    tmpl = await svc.get_template(template_id, cid)
    await svc.delete_template(tmpl)
    return {"detail": "Template deleted"}


# ── Assignments ───────────────────────────────────────

@router.post("/assignments", response_model=OnboardingAssignmentResponse)
async def create_assignment(
    payload: OnboardingAssignmentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> OnboardingAssignmentResponse:
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    assignment = await svc.create_assignment(
        company_id=cid,
        employee_id=payload.employee_id,
        template_id=payload.template_id,
        assigned_by_id=current_user.id,
        due_date=payload.due_date,
        notes=payload.notes,
    )
    return OnboardingAssignmentResponse(**svc._assignment_to_dict(assignment))


@router.get("/assignments", response_model=list[OnboardingAssignmentResponse])
async def list_assignments(
    employee_id: int | None = Query(default=None),
    status: OnboardingStatus | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> list[OnboardingAssignmentResponse]:
    cid = _company_id(current_user)
    rows = await OnboardingService(db).list_assignments(cid, employee_id, status)
    return [OnboardingAssignmentResponse(**r) for r in rows]


@router.get("/assignments/{assignment_id}", response_model=OnboardingAssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> OnboardingAssignmentResponse:
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    a = await svc.get_assignment(assignment_id, cid)
    return OnboardingAssignmentResponse(**svc._assignment_to_dict(a))


@router.patch("/assignments/{assignment_id}", response_model=OnboardingAssignmentResponse)
async def update_assignment(
    assignment_id: int,
    payload: OnboardingAssignmentUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> OnboardingAssignmentResponse:
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    a = await svc.get_assignment(assignment_id, cid)
    updated = await svc.update_assignment(a, payload.due_date, payload.notes)
    return OnboardingAssignmentResponse(**svc._assignment_to_dict(updated))


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    a = await svc.get_assignment(assignment_id, cid)
    await svc.delete_assignment(a)
    return {"detail": "Assignment deleted"}


@router.post("/assignments/{assignment_id}/tasks/{task_id}/toggle", response_model=OnboardingAssignmentResponse)
async def toggle_task(
    assignment_id: int,
    task_id: int,
    payload: TaskToggleRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> OnboardingAssignmentResponse:
    cid = _company_id(current_user)
    svc = OnboardingService(db)
    updated = await svc.toggle_task(assignment_id, task_id, cid, payload.note)
    return OnboardingAssignmentResponse(**svc._assignment_to_dict(updated))
