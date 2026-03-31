from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.core.security import hash_password, verify_password
from app.models import Role, User


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user(self, user_id: int) -> User:
        user = await self.db.scalar(
            select(User).options(selectinload(User.role)).where(User.id == user_id, User.deleted_at.is_(None))
        )
        if not user:
            raise AppException("User not found", status_code=404)
        return user

    async def update_profile(self, user: User, full_name: str | None) -> User:
        if full_name:
            user.full_name = full_name
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_avatar(self, user: User, avatar_url: str) -> User:
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise AppException("Old password is invalid", status_code=400)
        user.hashed_password = hash_password(new_password)
        await self.db.commit()

    async def create_candidate(self, email: str, full_name: str, default_password: str = "Candidate@123") -> User:
        existing = await self.db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))
        if existing:
            raise AppException("Email already registered", status_code=400)

        role = await self.db.scalar(select(Role).where(Role.name == "user"))
        if not role:
            raise AppException("Candidate role not found", status_code=500)

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(default_password),
            role_id=role.id,
            company_id=None,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
