import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models import Role, TokenBlacklist, User
from app.models.enums import UserRole


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_user(
        self,
        email: str,
        full_name: str,
        password: str,
        role: UserRole,
        company_id: int | None,
    ) -> User:
        existing = await self.db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))
        if existing:
            raise AppException("Email already registered")

        role_obj = await self.db.scalar(select(Role).where(Role.name == role.value))
        if not role_obj:
            raise AppException("Role not found", status_code=404)

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role_id=role_obj.id,
            company_id=company_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, email: str, password: str) -> dict[str, str]:
        user = await self.db.scalar(
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email, User.deleted_at.is_(None), User.is_active.is_(True))
        )
        if not user or not verify_password(password, user.hashed_password):
            raise AppException("Invalid credentials", status_code=401)

        access = create_access_token(subject=str(user.id), role=user.role.name)
        refresh = create_refresh_token(subject=str(user.id))
        return {"access_token": access, "refresh_token": refresh}

    async def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AppException("Invalid refresh token", status_code=401)

        jti = payload.get("jti")
        if jti and await self._is_blacklisted(jti):
            raise AppException("Token revoked", status_code=401)

        user_id = int(payload.get("sub"))
        user = await self.db.scalar(select(User).options(selectinload(User.role)).where(User.id == user_id, User.deleted_at.is_(None)))
        if not user:
            raise AppException("User not found", status_code=404)

        access = create_access_token(subject=str(user.id), role=user.role.name)
        new_refresh = create_refresh_token(subject=str(user.id))
        return {"access_token": access, "refresh_token": new_refresh}

    async def logout(self, token: str) -> None:
        payload = decode_token(token)
        jti = payload.get("jti")
        if not jti:
            raise AppException("Invalid token", status_code=401)

        exp_ts = payload.get("exp")
        if exp_ts is None:
            raise AppException("Invalid token expiry", status_code=401)

        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        blacklisted = TokenBlacklist(jti=jti, token_type=payload.get("type", "unknown"), expires_at=expires_at)
        self.db.add(blacklisted)
        await self.db.commit()

    async def _is_blacklisted(self, jti: str) -> bool:
        token = await self.db.scalar(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
        return token is not None

    async def login_or_register_social(
        self,
        *,
        provider: str,
        email: str,
        full_name: str,
        social_id: str,
        social_profile: dict[str, Any],
        role: UserRole | None,
    ) -> dict[str, str]:
        safe_provider = (provider or "").strip().lower()
        if safe_provider not in {"google", "linkedin"}:
            raise AppException("Unsupported OAuth provider", status_code=400)

        normalized_email = (email or "").strip().lower()
        normalized_social_id = (social_id or "").strip()
        normalized_full_name = (full_name or "").strip() or f"{safe_provider.title()} User"
        if not normalized_email or not normalized_social_id:
            raise AppException("email and social id are required", status_code=400)

        if not isinstance(social_profile, dict):
            raise AppException("social profile must be an object", status_code=400)

        social_id_field = f"{safe_provider}_id"
        social_profile_field = f"{safe_provider}_profile_json"

        user_by_social = await self.db.scalar(
            select(User)
            .options(selectinload(User.role))
            .where(getattr(User, social_id_field) == normalized_social_id, User.deleted_at.is_(None))
        )
        user_by_email = await self.db.scalar(
            select(User)
            .options(selectinload(User.role))
            .where(User.email == normalized_email, User.deleted_at.is_(None))
        )

        if user_by_social is None and role is None:
            raise AppException(
                "role is required for first social signup",
                status_code=400,
                error_code="role_required",
                meta={"allowed_roles": [UserRole.USER.value, UserRole.HR.value, UserRole.ADMIN.value]},
            )

        role_obj = None
        if role is not None:
            role_obj = await self.db.scalar(select(Role).where(Role.name == role.value))
            if not role_obj:
                raise AppException("Role not found", status_code=404)

        user = user_by_social or user_by_email
        if user is None:
            if role_obj is None:
                raise AppException("Role is required", status_code=400)

            user = User(
                email=normalized_email,
                full_name=normalized_full_name,
                hashed_password=hash_password(f"{safe_provider}:{normalized_social_id}:{normalized_email}"),
                role_id=role_obj.id,
            )
            setattr(user, social_id_field, normalized_social_id)
            setattr(user, social_profile_field, json.dumps(social_profile))
            self.db.add(user)
        else:
            # Preserve SOA behavior: first social link can override role if explicitly supplied.
            if user_by_social is None and user_by_email is not None and role_obj is not None:
                user.role_id = role_obj.id
                user.role = role_obj

            if not getattr(user, social_id_field):
                setattr(user, social_id_field, normalized_social_id)

            user.full_name = normalized_full_name
            setattr(user, social_profile_field, json.dumps(social_profile))

        await self.db.commit()
        await self.db.refresh(user)

        persisted_user = await self.db.scalar(select(User).options(selectinload(User.role)).where(User.id == user.id))
        if not persisted_user or not persisted_user.is_active or persisted_user.deleted_at is not None:
            raise AppException("User not found", status_code=401)

        access = create_access_token(subject=str(persisted_user.id), role=persisted_user.role.name)
        refresh = create_refresh_token(subject=str(persisted_user.id))
        return {"access_token": access, "refresh_token": refresh}
