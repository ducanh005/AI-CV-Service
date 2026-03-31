from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserGender, UserRole


class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    avatar_url: str | None
    date_of_birth: date | None
    phone: str | None
    address: str | None
    gender: UserGender | None
    education: str | None
    role: UserRole
    company_id: int | None


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    address: str | None = Field(default=None, max_length=255)
    gender: UserGender | None = None
    education: str | None = Field(default=None, max_length=255)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class CandidateCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)


class CandidateCreateResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
