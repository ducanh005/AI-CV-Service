from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import settings
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.integrations.rabbitmq_client import publish_event
from app.integrations.mock_ai_parser import extract_text_from_cv
from app.models import Application, CV, Job
from app.models import User
from app.models.enums import UserRole
from app.schemas.ai import (
    HRScoreCriteria,
    NotifyScreeningResultRequest,
    NotifyScreeningResultResponse,
    RankCandidatesAsyncItemResponse,
    RankCandidatesAsyncRequest,
    RankCandidatesAsyncStatusResponse,
    RankCandidatesAsyncSubmitResponse,
    RankCandidatesRequest,
    RankCandidatesResult,
    RankedCandidateResponse,
    ScoreCVRequest,
    ScoreCVResponse,
    ScoreUploadedCVResponse,
)
from app.services.ai_service import AICVScoringService
from app.services.async_scoring_service import AsyncScoringService
from app.services.notification_service import NotificationService
from app.services.storage_service import StorageService

router = APIRouter()


async def _ensure_hr_company_access(current_user: User, db: AsyncSession, company_id: int) -> None:
    if current_user.role.name != UserRole.HR.value:
        return

    if current_user.company_id is None:
        current_user.company_id = company_id
        await db.commit()
        await db.refresh(current_user)

    if current_user.company_id != company_id:
        raise AppException("Forbidden", status_code=403)


@router.post("/score-upload", response_model=ScoreUploadedCVResponse)
async def score_uploaded_cv(
    job_id: int = Form(...),
    min_score: float = Form(default=60.0),
    notify_candidates: bool = Form(default=False),
    candidate_email: str | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ScoreUploadedCVResponse:
    if min_score < 0 or min_score > 100:
        raise AppException("min_score must be between 0 and 100", status_code=400)

    job = await db.scalar(select(Job).where(Job.id == job_id, Job.deleted_at.is_(None)))
    if not job:
        raise AppException("Job not found", status_code=404)

    await _ensure_hr_company_access(current_user, db, job.company_id)

    allowed_pdf_types = {"application/pdf"}
    path = await StorageService.save_upload(file, settings.CV_DIR, allowed_pdf_types)
    cv_text = extract_text_from_cv(path)
    if not cv_text:
        raise AppException("Cannot extract text from uploaded PDF", status_code=400)

    criteria = HRScoreCriteria(required_skills=job.required_skills or [])
    ai_service = AICVScoringService(db)
    score, reasoning = await ai_service.score_with_ai(cv_text, job.description, criteria)
    passed = score >= min_score

    if notify_candidates:
        if not candidate_email:
            raise AppException("candidate_email is required when notify_candidates is true", status_code=400)
        NotificationService.send_screening_result(
            email=candidate_email,
            job_title=job.title,
            passed=passed,
            score=score,
            threshold=min_score,
        )

    return ScoreUploadedCVResponse(
        job_id=job.id,
        score=score,
        reasoning=reasoning,
        min_score=min_score,
        passed=passed,
        candidate_email=candidate_email,
    )


@router.post("/score-cv", response_model=ScoreCVResponse)
async def score_cv(
    payload: ScoreCVRequest,
    _: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ScoreCVResponse:
    ai_service = AICVScoringService(db)

    cv_text = payload.cv_text
    job_description = payload.job_description

    application: Application | None = None
    if payload.application_id is not None:
        application = await db.scalar(
            select(Application)
            .options(selectinload(Application.cv), selectinload(Application.job), selectinload(Application.candidate))
            .where(Application.id == payload.application_id)
        )
        if not application:
            raise AppException("Application not found", status_code=404)

    cv_obj: CV | None = None
    if payload.cv_id is not None:
        cv_obj = await db.scalar(select(CV).where(CV.id == payload.cv_id))
    elif application and application.cv:
        cv_obj = application.cv

    if not cv_text and cv_obj:
        cv_text = extract_text_from_cv(cv_obj.file_path)
    if not cv_text:
        raise AppException("Missing CV content. Provide cv_text or cv_id/application_id with CV file", status_code=400)

    if not job_description and application and application.job:
        job_description = application.job.description
    if not job_description:
        raise AppException("Missing job_description. Provide job_description or application_id linked to a job", status_code=400)

    score, reasoning = await ai_service.score_with_ai(cv_text, job_description, payload.criteria)

    if payload.application_id is not None:
        await ai_service.upsert_application_score(
            payload.application_id,
            score,
            reasoning,
            min_score=settings.AI_DEFAULT_PASS_SCORE,
        )

    return ScoreCVResponse(score=score, reasoning=reasoning)


@router.post("/rank-candidates", response_model=RankCandidatesResult)
async def rank_candidates(
    payload: RankCandidatesRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> RankCandidatesResult:
    job = await db.scalar(select(Job).where(Job.id == payload.job_id, Job.deleted_at.is_(None)))
    if not job:
        raise AppException("Job not found", status_code=404)

    await _ensure_hr_company_access(current_user, db, job.company_id)

    applications = (
        await db.scalars(
            select(Application)
            .options(selectinload(Application.cv), selectinload(Application.candidate))
            .where(Application.job_id == payload.job_id)
        )
    ).all()

    ai_service = AICVScoringService(db)
    criteria = payload.criteria
    if not criteria and job.required_skills:
        criteria = HRScoreCriteria(required_skills=job.required_skills)

    ranked_items: list[RankedCandidateResponse] = []
    total_scored = 0

    for application in applications:
        if not application.cv:
            continue

        cv_text = extract_text_from_cv(application.cv.file_path)
        if not cv_text:
            continue

        score, reasoning = await ai_service.score_with_ai(cv_text, job.description, criteria)
        total_scored += 1
        await ai_service.upsert_application_score(
            application.id,
            score,
            reasoning,
            min_score=payload.min_score,
        )

        passed = score >= payload.min_score
        if payload.notify_candidates and application.candidate:
            NotificationService.send_screening_result(
                email=application.candidate.email,
                job_title=job.title,
                passed=passed,
                score=score,
                threshold=payload.min_score,
            )

        if application.candidate:
            ranked_items.append(
                RankedCandidateResponse(
                    application_id=application.id,
                    candidate_id=application.candidate_id,
                    candidate_name=application.candidate.full_name,
                    candidate_email=application.candidate.email,
                    score=score,
                    passed=passed,
                    reasoning=reasoning,
                )
            )

    ranked_items.sort(key=lambda item: item.score, reverse=True)
    return RankCandidatesResult(
        total_scored=total_scored,
        total_passed=sum(1 for item in ranked_items if item.passed),
        min_score=payload.min_score,
        items=ranked_items,
    )


@router.post("/rank-candidates/async", response_model=RankCandidatesAsyncSubmitResponse)
async def rank_candidates_async(
    payload: RankCandidatesAsyncRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> RankCandidatesAsyncSubmitResponse:
    job = await db.scalar(select(Job).where(Job.id == payload.job_id, Job.deleted_at.is_(None)))
    if not job:
        raise AppException("Job not found", status_code=404)

    await _ensure_hr_company_access(current_user, db, job.company_id)

    applications = (
        await db.scalars(
            select(Application)
            .options(selectinload(Application.cv), selectinload(Application.candidate))
            .where(Application.job_id == payload.job_id)
        )
    ).all()

    criteria = payload.criteria
    if not criteria and job.required_skills:
        criteria = HRScoreCriteria(required_skills=job.required_skills)

    async_scoring_service = AsyncScoringService(db)
    scoring_job, items = await async_scoring_service.create_job(
        source_job=job,
        requested_by=current_user,
        min_score=payload.min_score,
        notify_candidates=payload.notify_candidates,
        criteria=criteria,
        applications=list(applications),
    )

    if not items:
        return RankCandidatesAsyncSubmitResponse(
            scoring_job_id=scoring_job.id,
            status=scoring_job.status,
            total_items=0,
            submitted_items=0,
            failed_items=0,
            queued_items=0,
        )

    request_item_by_application = {item.application_id: item for item in items}
    submitted_request_ids: set[str] = set()
    failed_to_queue: dict[str, str] = {}

    for application in applications:
        item = request_item_by_application.get(application.id)
        if not item or not application.cv:
            continue

        request_payload = {
            "request_id": item.request_id,
            "scoring_job_id": scoring_job.id,
            "application_id": application.id,
            "job_id": job.id,
            "cv_file_path": application.cv.file_path,
            "job_description": job.description or f"Job title: {job.title}",
            "min_score": payload.min_score,
            "criteria": criteria.model_dump() if criteria else None,
            "requested_by": current_user.id,
        }
        published = publish_event(
            rabbitmq_url=settings.RABBITMQ_URL,
            event_type="cv.scoring.request",
            payload=request_payload,
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key=settings.RABBITMQ_SCORING_REQUEST_ROUTING_KEY,
            correlation_id=item.request_id,
        )
        if published:
            submitted_request_ids.add(item.request_id)
        else:
            failed_to_queue[item.request_id] = "Failed to enqueue scoring request"

    scoring_job = await async_scoring_service.apply_submission_result(
        scoring_job_id=scoring_job.id,
        submitted_request_ids=submitted_request_ids,
        failed_to_queue=failed_to_queue,
    )

    pending_items = max(0, scoring_job.total_items - scoring_job.processed_items - scoring_job.failed_items)
    return RankCandidatesAsyncSubmitResponse(
        scoring_job_id=scoring_job.id,
        status=scoring_job.status,
        total_items=scoring_job.total_items,
        submitted_items=scoring_job.submitted_items,
        failed_items=scoring_job.failed_items,
        queued_items=pending_items,
    )


@router.get("/rank-candidates/async/{scoring_job_id}", response_model=RankCandidatesAsyncStatusResponse)
async def get_rank_candidates_async_status(
    scoring_job_id: str,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> RankCandidatesAsyncStatusResponse:
    async_scoring_service = AsyncScoringService(db)
    scoring_job, items = await async_scoring_service.get_job_with_items(scoring_job_id)

    source_job = scoring_job.source_job
    if not source_job or source_job.deleted_at is not None:
        raise AppException("Job not found", status_code=404)

    await _ensure_hr_company_access(current_user, db, source_job.company_id)

    response_items: list[RankCandidatesAsyncItemResponse] = []
    for item in items:
        application = item.application
        candidate = application.candidate if application else None
        score = item.score
        passed = (score >= scoring_job.min_score) if score is not None else None

        response_items.append(
            RankCandidatesAsyncItemResponse(
                request_id=item.request_id,
                application_id=item.application_id,
                candidate_id=application.candidate_id if application else None,
                candidate_name=candidate.full_name if candidate else None,
                candidate_email=candidate.email if candidate else None,
                status=item.status,
                score=score,
                passed=passed,
                reasoning=item.reasoning,
                provider=item.provider,
                error=item.error_message,
                processed_at=item.processed_at,
            )
        )

    status_order = {"processed": 0, "failed": 1, "queued": 2}
    response_items.sort(
        key=lambda row: (
            status_order.get(row.status, 3),
            -(row.score if row.score is not None else -1),
        )
    )

    pending_items = max(0, scoring_job.total_items - scoring_job.processed_items - scoring_job.failed_items)
    return RankCandidatesAsyncStatusResponse(
        scoring_job_id=scoring_job.id,
        status=scoring_job.status,
        job_id=scoring_job.source_job_id,
        min_score=scoring_job.min_score,
        notify_candidates=scoring_job.notify_candidates,
        total_items=scoring_job.total_items,
        submitted_items=scoring_job.submitted_items,
        processed_items=scoring_job.processed_items,
        failed_items=scoring_job.failed_items,
        pending_items=pending_items,
        items=response_items,
    )


@router.post("/notify-screening-result", response_model=NotifyScreeningResultResponse)
async def notify_screening_result(
    payload: NotifyScreeningResultRequest,
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> NotifyScreeningResultResponse:
    application = await db.scalar(
        select(Application)
        .options(selectinload(Application.job), selectinload(Application.candidate), selectinload(Application.ai_score))
        .where(Application.id == payload.application_id)
    )
    if not application:
        raise AppException("Application not found", status_code=404)

    if not application.job:
        raise AppException("Job not found", status_code=404)

    await _ensure_hr_company_access(current_user, db, application.job.company_id)

    if not application.candidate or not application.candidate.email:
        raise AppException("Candidate email not found", status_code=404)

    if not application.ai_score:
        raise AppException("AI score not found for this application", status_code=400)

    score = application.ai_score.score
    passed = score >= payload.min_score

    NotificationService.send_screening_result(
        email=application.candidate.email,
        job_title=application.job.title,
        passed=passed,
        score=score,
        threshold=payload.min_score,
    )

    return NotifyScreeningResultResponse(
        application_id=application.id,
        candidate_email=application.candidate.email,
        job_title=application.job.title,
        score=score,
        min_score=payload.min_score,
        passed=passed,
    )
