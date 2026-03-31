from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), index=True)

    role = relationship("Role", back_populates="users")
    company = relationship("Company", back_populates="hr_users")
    jobs = relationship("Job", back_populates="created_by")
    cvs = relationship("CV", back_populates="user")
    applications = relationship("Application", back_populates="candidate", foreign_keys="Application.candidate_id")
    reviewed_applications = relationship(
        "Application", back_populates="reviewed_by_user", foreign_keys="Application.reviewed_by"
    )
    interviews_as_candidate = relationship("Interview", back_populates="candidate", foreign_keys="Interview.candidate_id")
    interviews_as_hr = relationship("Interview", back_populates="hr", foreign_keys="Interview.hr_id")
