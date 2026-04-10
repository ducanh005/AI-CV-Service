from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models.enums import EmployeeStatus, UserRole
from app.models.user import User
from app.schemas.employee import EmployeeCreateRequest, EmployeeResponse, EmployeeUpdateRequest
from app.services.employee_service import EmployeeService

router = APIRouter()


@router.post("", response_model=EmployeeResponse)
async def create_employee(
    payload: EmployeeCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> EmployeeResponse:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    svc = EmployeeService(db)
    emp = await svc.create_employee(
        company_id=company_id,
        user_id=payload.user_id,
        department_id=payload.department_id,
        employee_code=payload.employee_code,
        position=payload.position,
        contract_type=payload.contract_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        identity_number=payload.identity_number,
        notes=payload.notes,
    )
    emp_full = await svc.get_employee(emp.id, company_id)
    return EmployeeResponse(**svc.to_response(emp_full))


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    department_id: int | None = Query(default=None),
    status: EmployeeStatus | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> list[EmployeeResponse]:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    rows = await EmployeeService(db).list_employees(company_id, department_id, status, search)
    return [EmployeeResponse(**r) for r in rows]


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> EmployeeResponse:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    svc = EmployeeService(db)
    emp = await svc.get_employee(employee_id, company_id)
    return EmployeeResponse(**svc.to_response(emp))


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    payload: EmployeeUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> EmployeeResponse:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    svc = EmployeeService(db)
    emp = await svc.get_employee(employee_id, company_id)
    updated = await svc.update_employee(
        emp,
        department_id=payload.department_id,
        position=payload.position,
        status=payload.status,
        contract_type=payload.contract_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        identity_number=payload.identity_number,
        notes=payload.notes,
    )
    return EmployeeResponse(**svc.to_response(updated))


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> dict:
    company_id = current_user.company_id
    if not company_id:
        raise AppException("User is not associated with any company", status_code=400)
    svc = EmployeeService(db)
    emp = await svc.get_employee(employee_id, company_id)
    await svc.delete_employee(emp)
    return {"detail": "Employee deleted"}
