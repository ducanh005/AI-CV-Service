from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CV(TimestampMixin, Base):
    __tablename__ = "cvs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_skills: Mapped[list[str] | None] = mapped_column(JSON)
    extracted_experience: Mapped[list[str] | None] = mapped_column(JSON)
    extracted_education: Mapped[list[str] | None] = mapped_column(JSON)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="cvs")
    applications = relationship("Application", back_populates="cv")
