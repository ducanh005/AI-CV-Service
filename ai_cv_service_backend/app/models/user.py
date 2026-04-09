from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserGender
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[UserGender | None] = mapped_column(String(20))
    education: Mapped[str | None] = mapped_column(String(255))
    google_id: Mapped[str | None] = mapped_column(String(128), index=True)
    google_profile_json: Mapped[str | None] = mapped_column(Text)
    linkedin_id: Mapped[str | None] = mapped_column(String(128), index=True)
    linkedin_profile_json: Mapped[str | None] = mapped_column(Text)
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
    employee = relationship("Employee", back_populates="user", uselist=False)
