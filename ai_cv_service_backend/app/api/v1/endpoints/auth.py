from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.core.limiter import limiter
from app.models.enums import UserRole
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    OAuthAuthorizeResponse,
    OAuthCodeExchangeRequest,
    RefreshTokenRequest,
    RegisterRequest,
    SocialRegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.services.social_oauth_service import SocialOAuthService

router = APIRouter()


def _extract_provider_token(authorization: str | None, query_token: str | None) -> str:
    if query_token:
        return query_token.strip()

    token = (authorization or "").strip()
    if not token:
        return ""

    if token.lower().startswith("bearer "):
        return token[7:].strip()
    return token


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


@router.get("/oauth/{provider}/authorize", response_model=OAuthAuthorizeResponse)
@limiter.limit("30/minute")
async def oauth_authorize(
    request: Request,
    provider: str,
    mode: str = Query(default="login"),
    state: str | None = Query(default=None, max_length=255),
) -> OAuthAuthorizeResponse:
    response = SocialOAuthService().build_authorize_url(provider=provider, mode=mode, state=state)
    return OAuthAuthorizeResponse(**response)


@router.get("/oauth/{provider}/callback")
async def oauth_callback_bridge(
    provider: str,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> RedirectResponse:
    redirect_url = SocialOAuthService().build_callback_redirect(
        provider,
        code=code,
        state=state,
        error=error,
        error_description=error_description,
    )
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/oauth/{provider}/token")
@limiter.limit("30/minute")
async def oauth_exchange_token(
    request: Request,
    provider: str,
    payload: OAuthCodeExchangeRequest,
) -> dict[str, Any]:
    return await SocialOAuthService().exchange_code(provider=provider, code=payload.code)


@router.get("/oauth/{provider}/profile")
@limiter.limit("60/minute")
async def oauth_get_profile(
    request: Request,
    provider: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    access_token: str | None = Query(default=None),
    id_token: str | None = Query(default=None),
) -> dict[str, Any]:
    token = _extract_provider_token(authorization, access_token)
    if not token:
        raise AppException("access token is required", status_code=400)
    return await SocialOAuthService().fetch_profile(provider=provider, access_token=token, id_token=id_token)


@router.post("/oauth/{provider}/register", response_model=TokenResponse)
@limiter.limit("30/minute")
async def oauth_register(
    request: Request,
    provider: str,
    payload: SocialRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    safe_provider = SocialOAuthService.normalize_provider(provider)

    if safe_provider == "google":
        social_id = payload.google_id
        social_profile = payload.google_profile or {}
        default_name = "Google User"
    else:
        social_id = payload.linkedin_id
        social_profile = payload.linkedin_profile or {}
        default_name = "LinkedIn User"

    if not social_id:
        raise AppException(f"{safe_provider}_id is required", status_code=400)

    tokens = await AuthService(db).login_or_register_social(
        provider=safe_provider,
        email=payload.email,
        full_name=payload.full_name or default_name,
        social_id=social_id,
        social_profile=social_profile,
        role=payload.role,
    )
    return TokenResponse(**tokens)
