from collections.abc import Callable

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.security import decode_token
from app.models import TokenBlacklist, User
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")

    jti = payload.get("jti")
    if jti:
        blacklisted = await db.scalar(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
        if blacklisted:
            raise HTTPException(status_code=401, detail="Token revoked")

    user_id = payload.get("sub")
    user = await db.scalar(
        select(User).options(selectinload(User.role)).where(User.id == int(user_id), User.deleted_at.is_(None), User.is_active.is_(True))
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_roles(*roles: UserRole) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        allowed = {role.value for role in roles}
        if current_user.role.name not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_checker
