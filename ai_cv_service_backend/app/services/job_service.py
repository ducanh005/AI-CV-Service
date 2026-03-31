from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import Company, Job
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
        await self.db.delete(job)
        await self.db.commit()

    async def list_jobs(
        self,
        page: int,
        page_size: int,
        status: JobStatus | None,
        location: str | None,
        q: str | None,
        skill: str | None,
    ) -> tuple[list[Job], int]:
        filters = [Job.deleted_at.is_(None)]
        if status:
            filters.append(Job.status == status.value)
        if location:
            filters.append(Job.location.ilike(f"%{location}%"))
        if skill:
            # Cast JSON skills to text for compatibility across different DB column types.
            filters.append(cast(Job.required_skills, String).ilike(f"%{skill}%"))

        if q:
            keyword = f"%{q}%"
            filters.append(
                or_(
                    Job.title.ilike(keyword),
                    Job.description.ilike(keyword),
                    Job.location.ilike(keyword),
                    Company.name.ilike(keyword),
                )
            )

        where_clause = and_(*filters)
        total_stmt = select(func.count(Job.id)).select_from(Job).join(Company, Company.id == Job.company_id).where(where_clause)
        total = await self.db.scalar(total_stmt)
        stmt = (
            select(Job)
            .join(Company, Company.id == Job.company_id)
            .where(where_clause)
            .order_by(Job.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        jobs = (await self.db.scalars(stmt)).all()
        return list(jobs), int(total or 0)
