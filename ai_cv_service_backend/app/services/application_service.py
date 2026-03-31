from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models import Application, CV, Job
from app.models.enums import ApplicationStatus


class ApplicationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def apply(self, job_id: int, candidate_id: int, cv_id: int) -> Application:
        job = await self.db.scalar(select(Job).where(Job.id == job_id, Job.deleted_at.is_(None)))
        if not job:
            raise AppException("Job not found", status_code=404)

        cv = await self.db.scalar(select(CV).where(CV.id == cv_id, CV.user_id == candidate_id))
        if not cv:
            raise AppException("CV not found", status_code=404)

        existing = await self.db.scalar(
            select(Application).where(Application.job_id == job_id, Application.candidate_id == candidate_id)
        )
        if existing:
            raise AppException("Already applied to this job", status_code=400)

        application = Application(job_id=job_id, candidate_id=candidate_id, cv_id=cv_id, status=ApplicationStatus.PENDING.value)
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def get_application(self, application_id: int) -> Application:
        application = await self.db.scalar(
            select(Application)
            .options(
                selectinload(Application.candidate),
                selectinload(Application.job).selectinload(Job.company),
                selectinload(Application.cv),
                selectinload(Application.ai_score),
            )
            .where(Application.id == application_id)
        )
        if not application:
            raise AppException("Application not found", status_code=404)
        return application

    async def review(
        self,
        application: Application,
        reviewer_id: int,
        status: ApplicationStatus,
        notes: str | None,
    ) -> Application:
        application.reviewed_by = reviewer_id
        application.status = status.value
        application.notes = notes
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def list_for_job(self, job_id: int, page: int, page_size: int) -> tuple[list[Application], int]:
        where_clause = and_(Application.job_id == job_id)
        total = await self.db.scalar(select(func.count(Application.id)).where(where_clause))
        applications = (
            await self.db.scalars(
                select(Application)
                .options(
                    selectinload(Application.candidate),
                    selectinload(Application.job).selectinload(Job.company),
                    selectinload(Application.cv),
                    selectinload(Application.ai_score),
                )
                .where(where_clause)
                .order_by(Application.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return list(applications), int(total or 0)

    async def list_for_candidate(self, candidate_id: int, page: int, page_size: int) -> tuple[list[Application], int]:
        where_clause = and_(Application.candidate_id == candidate_id)
        total = await self.db.scalar(select(func.count(Application.id)).where(where_clause))
        applications = (
            await self.db.scalars(
                select(Application)
                .options(
                    selectinload(Application.candidate),
                    selectinload(Application.job).selectinload(Job.company),
                    selectinload(Application.cv),
                    selectinload(Application.ai_score),
                )
                .where(where_clause)
                .order_by(Application.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return list(applications), int(total or 0)
