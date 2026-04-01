from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.core.security import hash_password, verify_password
from app.models import Application, CV, Job, Role, User
from app.models.enums import UserRole
from app.schemas.user import UpdateProfileRequest


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

    async def update_profile(self, user: User, payload: UpdateProfileRequest) -> User:
        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(user, key, value)
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

    async def find_candidate_by_email_for_hr(
        self,
        *,
        email: str,
        requester: User,
    ) -> tuple[User, CV | None]:
        candidate = await self.db.scalar(
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email, User.deleted_at.is_(None), User.is_active.is_(True))
        )
        if not candidate:
            raise AppException("Candidate not found", status_code=404)

        if not candidate.role or candidate.role.name != UserRole.USER.value:
            raise AppException("User is not a candidate", status_code=400)

        if requester.role.name == UserRole.HR.value:
            has_application_in_company = await self.db.scalar(
                select(Application.id)
                .join(Job, Job.id == Application.job_id)
                .where(
                    Application.candidate_id == candidate.id,
                    Job.company_id == requester.company_id,
                    Job.deleted_at.is_(None),
                )
                .limit(1)
            )
            if not has_application_in_company:
                raise AppException("Candidate not found", status_code=404)

        latest_cv = await self.db.scalar(
            select(CV)
            .where(CV.user_id == candidate.id)
            .order_by(CV.created_at.desc())
            .limit(1)
        )
        return candidate, latest_cv
