from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import settings
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.integrations.mock_ai_parser import extract_text_from_cv
from app.models import Application, CV, Job
from app.models import User
from app.models.enums import UserRole
from app.schemas.ai import HRScoreCriteria, RankCandidatesRequest, RankCandidatesResult, RankedCandidateResponse, ScoreCVRequest, ScoreCVResponse, ScoreUploadedCVResponse
from app.services.ai_service import AICVScoringService
from app.services.notification_service import NotificationService
from app.services.storage_service import StorageService

router = APIRouter()


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

    if current_user.role.name == UserRole.HR.value and current_user.company_id != job.company_id:
        raise AppException("Forbidden", status_code=403)

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
        await ai_service.upsert_application_score(payload.application_id, score, reasoning)

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

    if current_user.role.name == UserRole.HR.value and current_user.company_id != job.company_id:
        raise AppException("Forbidden", status_code=403)

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
        from app.schemas.ai import HRScoreCriteria

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
        await ai_service.upsert_application_score(application.id, score, reasoning)

        passed = score >= payload.min_score
        if payload.notify_candidates and application.candidate:
            NotificationService.send_screening_result(
                email=application.candidate.email,
                job_title=job.title,
                passed=passed,
                score=score,
                threshold=payload.min_score,
            )

        if passed and application.candidate:
            ranked_items.append(
                RankedCandidateResponse(
                    application_id=application.id,
                    candidate_id=application.candidate_id,
                    candidate_name=application.candidate.full_name,
                    candidate_email=application.candidate.email,
                    score=score,
                    reasoning=reasoning,
                )
            )

    ranked_items.sort(key=lambda item: item.score, reverse=True)
    return RankCandidatesResult(
        total_scored=total_scored,
        total_passed=len(ranked_items),
        min_score=payload.min_score,
        items=ranked_items,
    )
