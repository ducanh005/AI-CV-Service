from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db_session
from app.models import User
from app.schemas.cv import CVResponse
from app.services.cv_service import CVService
from app.services.storage_service import StorageService
from app.workers.tasks import parse_cv_background

router = APIRouter()


@router.post("/upload", response_model=CVResponse)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CVResponse:
    path = await StorageService.save_upload(file, settings.CV_DIR, StorageService.allowed_cv_types)
    cv = await CVService(db).create_cv(
        user_id=current_user.id,
        file_name=file.filename or "unknown",
        file_path=path,
        mime_type=file.content_type or "application/octet-stream",
    )
    parse_cv_background.delay(cv.id)
    return CVResponse.model_validate(cv)
