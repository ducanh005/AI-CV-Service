from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models import Application, Job, User
from app.models.enums import UserRole
from app.schemas.application import ApplicationResponse, ApplicationReviewRequest, ApplyJobRequest
from app.services.application_service import ApplicationService
from app.services.notification_service import NotificationService

router = APIRouter()


def _serialize_application(application) -> dict:
    return {
        "id": application.id,
        "job_id": application.job_id,
        "candidate_id": application.candidate_id,
        "cv_id": application.cv_id,
        "reviewed_by": application.reviewed_by,
        "status": application.status,
        "notes": application.notes,
        "created_at": application.created_at,
        "candidate_name": application.candidate.full_name if application.candidate else None,
        "candidate_email": application.candidate.email if application.candidate else None,
        "job_title": application.job.title if application.job else None,
        "company_name": application.job.company.name if application.job and application.job.company else None,
        "ai_score": application.ai_score.score if application.ai_score else None,
        "cv_file_name": application.cv.file_name if application.cv else None,
        "cv_file_path": application.cv.file_path if application.cv else None,
        "cv_mime_type": application.cv.mime_type if application.cv else None,
    }


@router.get("/hr-dashboard", response_model=dict)
async def hr_dashboard_metrics(
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    job_filter = [Job.deleted_at.is_(None)]
    if current_user.role.name == UserRole.HR.value:
        job_filter.append(Job.company_id == current_user.company_id)

    scoped_jobs = select(Job.id).where(*job_filter)

    total_candidates = int(
        await db.scalar(
            select(func.count(func.distinct(Application.candidate_id))).where(Application.job_id.in_(scoped_jobs))
        )
        or 0
    )
    open_jobs = int(
        await db.scalar(select(func.count(Job.id)).where(*job_filter, Job.status == "open"))
        or 0
    )
    hired = int(
        await db.scalar(
            select(func.count(Application.id)).where(Application.job_id.in_(scoped_jobs), Application.status == "accepted")
        )
        or 0
    )
    total_applications = int(
        await db.scalar(select(func.count(Application.id)).where(Application.job_id.in_(scoped_jobs)))
        or 0
    )

    hire_rate = round((hired / total_applications) * 100, 2) if total_applications else 0.0

    month_expr = func.to_char(Application.created_at, "YYYY-MM")
    monthly_rows = await db.execute(
        select(month_expr.label("month"), func.count(Application.id).label("count"))
        .where(Application.job_id.in_(scoped_jobs))
        .group_by("month")
        .order_by("month")
    )
    monthly_applications = [
        {"month": month, "count": count}
        for month, count in monthly_rows.all()
    ]

    status_rows = await db.execute(
        select(Application.status, func.count(Application.id))
        .where(Application.job_id.in_(scoped_jobs))
        .group_by(Application.status)
    )
    status_map = {status: int(count) for status, count in status_rows.all()}

    return {
        "overview": {
            "total_candidates": total_candidates,
            "open_jobs": open_jobs,
            "hired": hired,
            "hire_rate": hire_rate,
        },
        "monthly_applications": monthly_applications,
        "status_breakdown": {
            "pending": status_map.get("pending", 0),
            "accepted": status_map.get("accepted", 0),
            "rejected": status_map.get("rejected", 0),
        },
    }


@router.post("", response_model=ApplicationResponse)
async def apply_to_job(
    payload: ApplyJobRequest,
    current_user: User = Depends(require_roles(UserRole.USER)),
    db: AsyncSession = Depends(get_db_session),
) -> ApplicationResponse:
    service = ApplicationService(db)
    application = await service.apply(payload.job_id, current_user.id, payload.cv_id)

    job = await db.scalar(select(Job).where(Job.id == payload.job_id))
    if job:
        NotificationService.send_apply_success(current_user.email, job.title)

    created_application = await service.get_application(application.id)
    return ApplicationResponse.model_validate(_serialize_application(created_application))


@router.get("/me", response_model=dict)
async def list_my_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.USER)),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = ApplicationService(db)
    applications, total = await service.list_for_candidate(current_user.id, page, page_size)

    items = [_serialize_application(a) for a in applications]
    stats = {
        "total": total,
        "pending": int(
            await db.scalar(
                select(func.count()).where(
                    Application.candidate_id == current_user.id,
                    Application.status == "pending",
                )
            )
            or 0
        ),
        "accepted": int(
            await db.scalar(
                select(func.count()).where(
                    Application.candidate_id == current_user.id,
                    Application.status == "accepted",
                )
            )
            or 0
        ),
        "rejected": int(
            await db.scalar(
                select(func.count()).where(
                    Application.candidate_id == current_user.id,
                    Application.status == "rejected",
                )
            )
            or 0
        ),
    }
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "stats": stats,
    }


@router.get("/job/{job_id}", response_model=dict)
async def list_job_applications(
    job_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    job = await db.scalar(select(Job).where(Job.id == job_id, Job.deleted_at.is_(None)))
    if not job:
        raise AppException("Job not found", status_code=404)

    if current_user.role.name == UserRole.HR.value and current_user.company_id != job.company_id:
        raise AppException("Forbidden", status_code=403)

    service = ApplicationService(db)
    applications, total = await service.list_for_job(job_id, page, page_size)
    return {
        "items": [ApplicationResponse.model_validate(_serialize_application(a)).model_dump() for a in applications],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/{application_id}/review", response_model=ApplicationResponse)
async def review_application(
    application_id: int,
    payload: ApplicationReviewRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ApplicationResponse:
    service = ApplicationService(db)
    application = await service.get_application(application_id)

    job = await db.scalar(select(Job).where(Job.id == application.job_id, Job.deleted_at.is_(None)))
    if not job:
        raise AppException("Job not found", status_code=404)

    if current_user.role.name == UserRole.HR.value and current_user.company_id != job.company_id:
        raise AppException("Forbidden", status_code=403)

    updated = await service.review(application, current_user.id, payload.status, payload.notes)
    refreshed = await service.get_application(updated.id)
    return ApplicationResponse.model_validate(_serialize_application(refreshed))
