from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.mock_ai_parser import parse_cv_file
from app.models import CV


class CVService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_cv(self, user_id: int, file_name: str, file_path: str, mime_type: str) -> CV:
        parsed = parse_cv_file(file_path)
        cv = CV(
            user_id=user_id,
            file_name=file_name,
            file_path=file_path,
            mime_type=mime_type,
            extracted_skills=parsed["skills"],
            extracted_experience=parsed["experience"],
            extracted_education=parsed["education"],
        )
        self.db.add(cv)
        await self.db.commit()
        await self.db.refresh(cv)
        return cv

    async def get_cv(self, cv_id: int) -> CV | None:
        return await self.db.scalar(select(CV).where(CV.id == cv_id))
