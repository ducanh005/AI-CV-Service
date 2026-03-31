from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.core.config import settings
from app.models import User
from app.models.enums import UserRole
from app.schemas.user import CandidateCreateRequest, CandidateCreateResponse, ChangePasswordRequest, UpdateProfileRequest, UserProfileResponse
from app.services.storage_service import StorageService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        role=UserRole(current_user.role.name),
        company_id=current_user.company_id,
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    user = await UserService(db).update_profile(current_user, payload.full_name)
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role=UserRole(user.role.name),
        company_id=user.company_id,
    )


@router.post("/me/avatar", response_model=UserProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    path = await StorageService.save_upload(file, settings.AVATAR_DIR, StorageService.allowed_avatar_types)
    user = await UserService(db).update_avatar(current_user, path)
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role=UserRole(user.role.name),
        company_id=user.company_id,
    )


@router.post("/me/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    if payload.old_password == payload.new_password:
        raise AppException("New password must differ from old password")

    await UserService(db).change_password(current_user, payload.old_password, payload.new_password)
    return {"message": "Password changed successfully"}


@router.post("/candidates", response_model=CandidateCreateResponse)
async def create_candidate(
    payload: CandidateCreateRequest,
    _: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> CandidateCreateResponse:
    user = await UserService(db).create_candidate(email=payload.email, full_name=payload.full_name)
    return CandidateCreateResponse(id=user.id, email=user.email, full_name=user.full_name)
