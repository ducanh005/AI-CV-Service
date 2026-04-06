from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.USER
    company_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    token: str


class OAuthAuthorizeResponse(BaseModel):
    auth_url: str
    state: str
    mode: str


class OAuthCodeExchangeRequest(BaseModel):
    code: str = Field(min_length=4)


class SocialRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=120)
    role: UserRole | None = None
    google_id: str | None = Field(default=None, min_length=2, max_length=128)
    linkedin_id: str | None = Field(default=None, min_length=2, max_length=128)
    google_profile: dict[str, Any] | None = None
    linkedin_profile: dict[str, Any] | None = None
