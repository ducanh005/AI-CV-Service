from pathlib import Path
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.mock_ai_parser import extract_text_from_cv
from app.schemas.ai import HRScoreCriteria
from app.services.ai_service import AICVScoringService
from app.services.async_scoring_service import AsyncScoringService
from app.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class ScoringRequestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.async_scoring_service = AsyncScoringService(db)
        self.ai_service = AICVScoringService(db)

    @staticmethod
    def _parse_criteria(criteria_payload: object) -> HRScoreCriteria | None:
        if criteria_payload is None:
            return None
        if isinstance(criteria_payload, dict):
            return HRScoreCriteria.model_validate(criteria_payload)
        raise ValueError("Invalid criteria payload")

    @staticmethod
    def _resolve_cv_file_path(raw_path: str) -> str:
        incoming_path = (raw_path or "").strip()
        if not incoming_path:
            return ""

        source_path = Path(incoming_path)
        candidates: list[Path] = []

        if source_path.is_absolute():
            candidates.append(source_path)
        else:
            app_root = Path(__file__).resolve().parents[2]
            candidates.extend(
                [
                    source_path,
                    app_root / source_path,
                ]
            )

            has_upload_prefix = incoming_path.startswith(f"{settings.UPLOAD_DIR}/") or incoming_path.startswith(
                f"{settings.UPLOAD_DIR}\\"
            )
            if not has_upload_prefix:
                candidates.append(app_root / settings.UPLOAD_DIR / source_path)

        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except Exception:
                continue

            if resolved.exists():
                return str(resolved)

        # Keep best-effort absolute path for downstream logging.
        if source_path.is_absolute():
            return str(source_path)
        return str((Path(__file__).resolve().parents[2] / source_path).resolve())

    async def process_request(self, payload: dict) -> None:
        request_id = str(payload.get("request_id", "")).strip()
        if not request_id:
            logger.warning("Scoring request payload missing request_id")
            return

        try:
            cv_file_path = self._resolve_cv_file_path(str(payload.get("cv_file_path", "")))
            if not cv_file_path:
                raise ValueError("Missing cv_file_path")

            job_description = str(payload.get("job_description", "")).strip()
            if not job_description:
                raise ValueError("Missing job_description")

            criteria = self._parse_criteria(payload.get("criteria"))
            cv_text = extract_text_from_cv(cv_file_path)
            if not cv_text:
                raise ValueError(f"Cannot extract CV text from path: {cv_file_path}")

            score, reasoning = await self.ai_service.score_with_ai(cv_text, job_description, criteria)
            item = await self.async_scoring_service.record_result(
                request_id=request_id,
                score=score,
                reasoning=reasoning,
                provider="gemini",
            )
            if not item:
                logger.warning("No scoring item found for request_id=%s", request_id)
                return

            await self.ai_service.upsert_application_score(
                application_id=item.application_id,
                score=score,
                reasoning=reasoning,
                min_score=item.scoring_job.min_score,
            )

            if item.scoring_job.notify_candidates and item.application and item.application.candidate and item.application.job:
                passed = score >= item.scoring_job.min_score
                NotificationService.send_screening_result(
                    email=item.application.candidate.email,
                    job_title=item.application.job.title,
                    passed=passed,
                    score=score,
                    threshold=item.scoring_job.min_score,
                )
        except Exception as exc:
            try:
                await self.async_scoring_service.record_failed(request_id=request_id, error_message=str(exc))
            except Exception:
                logger.exception("Failed to persist scoring failure for request_id=%s", request_id)

            logger.exception("Scoring request failed for request_id=%s", request_id)
