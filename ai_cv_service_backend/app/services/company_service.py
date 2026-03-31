from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models import Company


class CompanyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_company(self, name: str, website: str | None, description: str | None, location: str | None) -> Company:
        existing = await self.db.scalar(select(Company).where(Company.name == name, Company.deleted_at.is_(None)))
        if existing:
            raise AppException("Company already exists", status_code=400)

        company = Company(name=name, website=website, description=description, location=location)
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def get_company(self, company_id: int) -> Company:
        company = await self.db.scalar(select(Company).where(Company.id == company_id, Company.deleted_at.is_(None)))
        if not company:
            raise AppException("Company not found", status_code=404)
        return company

    async def update_company(self, company: Company, website: str | None, description: str | None, location: str | None) -> Company:
        company.website = website
        company.description = description
        company.location = location
        await self.db.commit()
        await self.db.refresh(company)
        return company
