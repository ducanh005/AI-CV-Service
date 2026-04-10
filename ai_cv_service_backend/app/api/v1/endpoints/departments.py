from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.department import DepartmentCreateRequest, DepartmentResponse, DepartmentUpdateRequest
from app.services.department_service import DepartmentService

router = APIRouter()


@router.post("", response_model=DepartmentResponse)
async def create_department(
    payload: DepartmentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> DepartmentResponse:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    dept = await DepartmentService(db).create_department(
        company_id=company_id,
        name=payload.name,
        description=payload.description,
        manager_id=payload.manager_id,
    )
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        company_id=dept.company_id,
        manager_id=dept.manager_id,
    )


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> list[DepartmentResponse]:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    rows = await DepartmentService(db).list_departments(company_id)
    return [DepartmentResponse(**r) for r in rows]


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> DepartmentResponse:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    dept = await DepartmentService(db).get_department(department_id, company_id)
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        company_id=dept.company_id,
        manager_id=dept.manager_id,
    )


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    payload: DepartmentUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> DepartmentResponse:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    svc = DepartmentService(db)
    dept = await svc.get_department(department_id, company_id)
    updated = await svc.update_department(dept, payload.name, payload.description, payload.manager_id)
    return DepartmentResponse(
        id=updated.id,
        name=updated.name,
        description=updated.description,
        company_id=updated.company_id,
        manager_id=updated.manager_id,
    )


@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> dict:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    svc = DepartmentService(db)
    dept = await svc.get_department(department_id, company_id)
    await svc.delete_department(dept)
    return {"detail": "Department deleted"}
