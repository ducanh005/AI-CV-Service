from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ContractType, EmployeeStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Employee(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=EmployeeStatus.ACTIVE.value, nullable=False)
    contract_type: Mapped[str] = mapped_column(String(20), default=ContractType.PERMANENT.value, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    identity_number: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    company = relationship("Company", back_populates="employees")
    onboarding_assignments = relationship("OnboardingAssignment", back_populates="employee")
    attendances = relationship("Attendance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
