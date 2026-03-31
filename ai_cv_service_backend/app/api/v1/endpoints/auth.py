from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.limiter import limiter
from app.models.enums import UserRole
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshTokenRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
@limiter.limit("20/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    auth_service = AuthService(db)
    user = await auth_service.register_user(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=payload.role,
        company_id=payload.company_id,
    )
    tokens = await auth_service.login(payload.email, payload.password)
    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("30/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    tokens = await AuthService(db).login(payload.email, payload.password)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    tokens = await AuthService(db).refresh_access_token(payload.refresh_token)
    return TokenResponse(**tokens)


@router.post("/logout")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    await AuthService(db).logout(payload.token)
    return {"message": "Logged out successfully"}
