from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role
from app.models.enums import UserRole


async def seed_default_roles(db: AsyncSession) -> None:
    existing_roles = {
        role.name for role in (await db.scalars(select(Role))).all()
    }

    for role in UserRole:
        if role.value not in existing_roles:
            db.add(Role(name=role.value, description=f"System role: {role.value}"))

    await db.commit()
