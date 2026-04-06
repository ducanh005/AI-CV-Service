from sqlalchemy import text
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


async def ensure_user_profile_columns(db: AsyncSession) -> None:
    # Keep existing deployments compatible when new profile fields are introduced.
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS gender VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS education VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(128)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_profile_json TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS linkedin_id VARCHAR(128)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS linkedin_profile_json TEXT",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_google_id_nonnull ON users (google_id) WHERE google_id IS NOT NULL",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_linkedin_id_nonnull ON users (linkedin_id) WHERE linkedin_id IS NOT NULL",
    ]
    for stmt in statements:
        await db.execute(text(stmt))
    await db.commit()
