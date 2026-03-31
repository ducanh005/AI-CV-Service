from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import Job
from app.models.enums import JobStatus


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_job(self, **kwargs) -> Job:
        job = Job(**kwargs)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job(self, job_id: int) -> Job:
        job = await self.db.scalar(select(Job).where(Job.id == job_id, Job.deleted_at.is_(None)))
        if not job:
            raise AppException("Job not found", status_code=404)
        return job

    async def update_job(self, job: Job, payload: dict) -> Job:
        for key, value in payload.items():
            if value is not None:
                setattr(job, key, value)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def delete_job(self, job: Job) -> None:
        job.deleted_at = func.now()
        await self.db.commit()

    async def list_jobs(
        self,
        page: int,
        page_size: int,
        status: JobStatus | None,
        location: str | None,
        skill: str | None,
    ) -> tuple[list[Job], int]:
        filters = [Job.deleted_at.is_(None)]
        if status:
            filters.append(Job.status == status.value)
        if location:
            filters.append(Job.location.ilike(f"%{location}%"))
        if skill:
            filters.append(Job.required_skills.contains([skill]))

        where_clause = and_(*filters)
        total = await self.db.scalar(select(func.count(Job.id)).where(where_clause))
        stmt = (
            select(Job)
            .where(where_clause)
            .order_by(Job.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        jobs = (await self.db.scalars(stmt)).all()
        return list(jobs), int(total or 0)
