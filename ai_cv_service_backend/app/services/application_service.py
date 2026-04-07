from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppException
from app.models import Application, CV, Job
from app.models.enums import ApplicationStatus


class ApplicationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _sync_scored_pending_statuses(
        self,
        applications: list[Application],
        min_score: float | None = None,
    ) -> None:
        threshold = settings.AI_DEFAULT_PASS_SCORE if min_score is None else min_score
        threshold = max(0.0, min(100.0, float(threshold)))

        changed = False
        for application in applications:
            if application.status != ApplicationStatus.PENDING.value:
                continue
            if not application.ai_score:
                continue

            application.status = (
                ApplicationStatus.ACCEPTED.value
                if application.ai_score.score >= threshold
                else ApplicationStatus.REJECTED.value
            )
            changed = True

        if changed:
            await self.db.commit()

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

        await self._sync_scored_pending_statuses([application])
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
        await self._sync_scored_pending_statuses(list(applications))
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
        await self._sync_scored_pending_statuses(list(applications))
        return list(applications), int(total or 0)

    async def list_for_company(self, company_id: int, page: int, page_size: int) -> tuple[list[Application], int]:
        where_clause = and_(
            Application.job_id == Job.id,
            Job.company_id == company_id,
            Job.deleted_at.is_(None),
        )
        total = await self.db.scalar(
            select(func.count(Application.id)).select_from(Application, Job).where(where_clause)
        )
        applications = (
            await self.db.scalars(
                select(Application)
                .join(Job, Job.id == Application.job_id)
                .options(
                    selectinload(Application.candidate),
                    selectinload(Application.job).selectinload(Job.company),
                    selectinload(Application.cv),
                    selectinload(Application.ai_score),
                )
                .where(Job.company_id == company_id, Job.deleted_at.is_(None))
                .order_by(Application.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        await self._sync_scored_pending_statuses(list(applications))
        return list(applications), int(total or 0)

    async def list_all(self, page: int, page_size: int) -> tuple[list[Application], int]:
        total = await self.db.scalar(select(func.count(Application.id)))
        applications = (
            await self.db.scalars(
                select(Application)
                .options(
                    selectinload(Application.candidate),
                    selectinload(Application.job).selectinload(Job.company),
                    selectinload(Application.cv),
                    selectinload(Application.ai_score),
                )
                .order_by(Application.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        await self._sync_scored_pending_statuses(list(applications))
        return list(applications), int(total or 0)
