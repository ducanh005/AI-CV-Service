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


async def ensure_contract_columns(db: AsyncSession) -> None:
    # Keep contract module additive for older deployments.
    statements = [
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS contract_code VARCHAR(64)",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS title VARCHAR(160)",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS contract_type VARCHAR(32)",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS status VARCHAR(20)",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS start_date DATE",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS end_date DATE",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS signed_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS salary_amount INTEGER",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS salary_currency VARCHAR(8)",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS benefits TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS terms TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS notes TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS termination_reason TEXT",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS terminated_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS version INTEGER",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS is_current BOOLEAN",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS employee_id INTEGER",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS company_id INTEGER",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS source_application_id INTEGER",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS previous_contract_id INTEGER",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS created_by_id INTEGER",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_contracts_contract_code ON contracts (contract_code)",
        "CREATE INDEX IF NOT EXISTS idx_contracts_company_status ON contracts (company_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_contracts_company_current ON contracts (company_id, is_current)",
        "CREATE INDEX IF NOT EXISTS idx_contracts_end_date ON contracts (end_date)",
        "CREATE INDEX IF NOT EXISTS idx_contract_documents_contract_id ON contract_documents (contract_id)",
        "CREATE INDEX IF NOT EXISTS idx_contract_status_histories_contract_id ON contract_status_histories (contract_id)",
    ]
    for stmt in statements:
        await db.execute(text(stmt))

    # Default backfill for non-null columns introduced later.
    await db.execute(text("UPDATE contracts SET salary_currency = 'VND' WHERE salary_currency IS NULL"))
    await db.execute(text("UPDATE contracts SET version = 1 WHERE version IS NULL"))
    await db.execute(text("UPDATE contracts SET is_current = TRUE WHERE is_current IS NULL"))
    # Normalize legacy draft statuses into supported lifecycle statuses.
    await db.execute(
        text(
            "UPDATE contracts SET status = 'expired' "
            "WHERE status = 'draft' AND end_date IS NOT NULL AND end_date < CURRENT_DATE"
        )
    )
    await db.execute(
        text(
            "UPDATE contracts SET status = 'active' "
            "WHERE status = 'draft' AND (end_date IS NULL OR end_date >= CURRENT_DATE)"
        )
    )
    await db.commit()
