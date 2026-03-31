from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models import Company, User
from app.models.enums import JobStatus, UserRole
from app.schemas.job import JobCreateRequest, JobResponse, JobUpdateRequest
from app.services.job_service import JobService

router = APIRouter()


@router.post("", response_model=JobResponse)
async def create_job(
    payload: JobCreateRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> JobResponse:
    if current_user.role.name == UserRole.HR.value and not current_user.company_id:
        raise AppException("HR user must belong to a company")

    company_id = current_user.company_id
    if current_user.role.name == UserRole.ADMIN.value:
        company_id = payload.company_id or current_user.company_id
        if company_id is None:
            fallback_company = await db.scalar(select(Company).where(Company.deleted_at.is_(None)).order_by(Company.id.asc()))
            if not fallback_company:
                raise AppException("No company found. Create a company before posting jobs.", status_code=400)
            company_id = fallback_company.id

    job = await JobService(db).create_job(
        title=payload.title,
        description=payload.description,
        required_skills=payload.required_skills,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        location=payload.location,
        status=payload.status.value,
        company_id=company_id,
        created_by_id=current_user.id,
    )
    return JobResponse.model_validate(job)


@router.get("", response_model=dict)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: JobStatus | None = Query(default=None),
    location: str | None = Query(default=None),
    q: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    jobs, total = await JobService(db).list_jobs(
        page=page,
        page_size=page_size,
        status=status,
        location=location,
        q=q,
        skill=skill,
    )
    return {
        "items": [JobResponse.model_validate(job).model_dump() for job in jobs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    payload: JobUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> JobResponse:
    job = await JobService(db).get_job(job_id)
    if current_user.role.name == UserRole.HR.value and current_user.company_id != job.company_id:
        raise AppException("You can only manage jobs in your company", status_code=403)

    updated = await JobService(db).update_job(job, payload.model_dump(exclude_none=True))
    return JobResponse.model_validate(updated)


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    job = await JobService(db).get_job(job_id)
    if current_user.role.name == UserRole.HR.value and current_user.company_id != job.company_id:
        raise AppException("You can only manage jobs in your company", status_code=403)

    await JobService(db).delete_job(job)
    return {"message": "Job deleted"}
