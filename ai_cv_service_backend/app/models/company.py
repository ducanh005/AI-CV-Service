from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Company(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))

    hr_users = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company")
    departments = relationship("Department", back_populates="company")
    employees = relationship("Employee", back_populates="company")
    onboarding_templates = relationship("OnboardingTemplate", back_populates="company")
    onboarding_assignments = relationship("OnboardingAssignment", back_populates="company")
    attendances = relationship("Attendance", back_populates="company")
    leave_requests = relationship("LeaveRequest", back_populates="company")
