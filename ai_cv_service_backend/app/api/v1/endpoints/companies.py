from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models import User
from app.models.enums import UserRole
from app.schemas.company import CompanyCreateRequest, CompanyResponse, CompanyUpdateRequest
from app.services.company_service import CompanyService

router = APIRouter()


@router.post("", response_model=CompanyResponse)
async def create_company(
    payload: CompanyCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> CompanyResponse:
    company = await CompanyService(db).create_company(
        name=payload.name,
        website=payload.website,
        description=payload.description,
        location=payload.location,
    )
    return CompanyResponse.model_validate(company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> CompanyResponse:
    company = await CompanyService(db).get_company(company_id)
    return CompanyResponse.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    payload: CompanyUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
) -> CompanyResponse:
    company = await CompanyService(db).get_company(company_id)
    if current_user.role.name == UserRole.HR.value and current_user.company_id != company_id:
        raise AppException("HR can only update their own company", status_code=403)

    updated = await CompanyService(db).update_company(
        company=company,
        website=payload.website,
        description=payload.description,
        location=payload.location,
    )
    return CompanyResponse.model_validate(updated)
