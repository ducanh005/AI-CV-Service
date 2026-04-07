from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models import Application, Job, ScoringJob, ScoringJobItem, User
from app.schemas.ai import HRScoreCriteria


class AsyncScoringService:
    JOB_STATUS_QUEUED = "queued"
    JOB_STATUS_PROCESSING = "processing"
    JOB_STATUS_COMPLETED = "completed"
    JOB_STATUS_PARTIAL_FAILED = "partial_failed"
    JOB_STATUS_FAILED = "failed"

    ITEM_STATUS_QUEUED = "queued"
    ITEM_STATUS_PROCESSED = "processed"
    ITEM_STATUS_FAILED = "failed"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_job(
        self,
        source_job: Job,
        requested_by: User,
        min_score: float,
        notify_candidates: bool,
        criteria: HRScoreCriteria | None,
        applications: list[Application],
    ) -> tuple[ScoringJob, list[ScoringJobItem]]:
        scoring_job = ScoringJob(
            id=str(uuid4()),
            source_job_id=source_job.id,
            requested_by=requested_by.id,
            min_score=min_score,
            notify_candidates=notify_candidates,
            status=self.JOB_STATUS_QUEUED,
            total_items=0,
            submitted_items=0,
            processed_items=0,
            failed_items=0,
            criteria_json=criteria.model_dump() if criteria else None,
        )
        self.db.add(scoring_job)

        items: list[ScoringJobItem] = []
        for application in applications:
            if not application.cv:
                continue

            item = ScoringJobItem(
                scoring_job_id=scoring_job.id,
                application_id=application.id,
                request_id=str(uuid4()),
                status=self.ITEM_STATUS_QUEUED,
            )
            self.db.add(item)
            items.append(item)

        scoring_job.total_items = len(items)
        if scoring_job.total_items == 0:
            scoring_job.status = self.JOB_STATUS_COMPLETED

        await self.db.commit()
        await self.db.refresh(scoring_job)
        return scoring_job, items

    async def apply_submission_result(
        self,
        scoring_job_id: str,
        submitted_request_ids: set[str],
        failed_to_queue: dict[str, str],
    ) -> ScoringJob:
        scoring_job = await self.get_job(scoring_job_id)
        if not scoring_job:
            raise AppException("Scoring job not found", status_code=404)

        if failed_to_queue:
            failed_items = (
                await self.db.scalars(
                    select(ScoringJobItem).where(
                        ScoringJobItem.scoring_job_id == scoring_job_id,
                        ScoringJobItem.request_id.in_(list(failed_to_queue.keys())),
                    )
                )
            ).all()
            for item in failed_items:
                item.status = self.ITEM_STATUS_FAILED
                item.error_message = failed_to_queue[item.request_id][:1000]
                item.attempts += 1
                item.processed_at = datetime.now(timezone.utc)

        scoring_job.submitted_items = len(submitted_request_ids)
        await self._recalculate_job_progress(scoring_job)
        await self.db.commit()
        await self.db.refresh(scoring_job)
        return scoring_job

    async def get_job(self, scoring_job_id: str) -> ScoringJob | None:
        return await self.db.scalar(select(ScoringJob).where(ScoringJob.id == scoring_job_id))

    async def get_job_with_items(self, scoring_job_id: str) -> tuple[ScoringJob, list[ScoringJobItem]]:
        scoring_job = await self.db.scalar(
            select(ScoringJob)
            .options(selectinload(ScoringJob.source_job))
            .where(ScoringJob.id == scoring_job_id)
        )
        if not scoring_job:
            raise AppException("Scoring job not found", status_code=404)

        items = (
            await self.db.scalars(
                select(ScoringJobItem)
                .options(
                    selectinload(ScoringJobItem.application).selectinload(Application.candidate),
                    selectinload(ScoringJobItem.application).selectinload(Application.job),
                )
                .where(ScoringJobItem.scoring_job_id == scoring_job_id)
            )
        ).all()

        return scoring_job, list(items)

    async def record_result(
        self,
        request_id: str,
        score: float,
        reasoning: str,
        provider: str | None,
    ) -> ScoringJobItem | None:
        item = await self.db.scalar(
            select(ScoringJobItem)
            .options(
                selectinload(ScoringJobItem.scoring_job),
                selectinload(ScoringJobItem.application).selectinload(Application.candidate),
                selectinload(ScoringJobItem.application).selectinload(Application.job),
            )
            .where(ScoringJobItem.request_id == request_id)
        )
        if not item:
            return None

        if item.status != self.ITEM_STATUS_PROCESSED:
            item.status = self.ITEM_STATUS_PROCESSED
            item.score = score
            item.reasoning = reasoning[:2000]
            item.provider = provider
            item.error_message = None
            item.attempts += 1
            item.processed_at = datetime.now(timezone.utc)
            await self._recalculate_job_progress(item.scoring_job)
            await self.db.commit()
            await self.db.refresh(item)

        return item

    async def record_failed(self, request_id: str, error_message: str) -> ScoringJobItem | None:
        item = await self.db.scalar(
            select(ScoringJobItem)
            .options(selectinload(ScoringJobItem.scoring_job))
            .where(ScoringJobItem.request_id == request_id)
        )
        if not item:
            return None

        if item.status != self.ITEM_STATUS_PROCESSED:
            item.status = self.ITEM_STATUS_FAILED
            item.error_message = error_message[:2000]
            item.attempts += 1
            item.processed_at = datetime.now(timezone.utc)
            await self._recalculate_job_progress(item.scoring_job)
            await self.db.commit()
            await self.db.refresh(item)

        return item

    async def _recalculate_job_progress(self, scoring_job: ScoringJob) -> None:
        processed_items = int(
            await self.db.scalar(
                select(func.count(ScoringJobItem.id)).where(
                    ScoringJobItem.scoring_job_id == scoring_job.id,
                    ScoringJobItem.status == self.ITEM_STATUS_PROCESSED,
                )
            )
            or 0
        )
        failed_items = int(
            await self.db.scalar(
                select(func.count(ScoringJobItem.id)).where(
                    ScoringJobItem.scoring_job_id == scoring_job.id,
                    ScoringJobItem.status == self.ITEM_STATUS_FAILED,
                )
            )
            or 0
        )

        scoring_job.processed_items = processed_items
        scoring_job.failed_items = failed_items

        if scoring_job.total_items == 0:
            scoring_job.status = self.JOB_STATUS_COMPLETED
            return

        done = processed_items + failed_items
        if done == 0:
            scoring_job.status = self.JOB_STATUS_QUEUED
            return

        if done < scoring_job.total_items:
            scoring_job.status = self.JOB_STATUS_PROCESSING
            return

        if processed_items == scoring_job.total_items:
            scoring_job.status = self.JOB_STATUS_COMPLETED
        elif processed_items == 0:
            scoring_job.status = self.JOB_STATUS_FAILED
        else:
            scoring_job.status = self.JOB_STATUS_PARTIAL_FAILED
