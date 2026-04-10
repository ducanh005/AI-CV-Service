from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import OnboardingStatus, TaskPriority
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class OnboardingTemplate(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "onboarding_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    company = relationship("Company", back_populates="onboarding_templates")
    tasks: Mapped[list["OnboardingTask"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="OnboardingTask.order"
    )
    assignments: Mapped[list["OnboardingAssignment"]] = relationship(back_populates="template")


class OnboardingTask(TimestampMixin, Base):
    __tablename__ = "onboarding_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default=TaskPriority.MEDIUM.value, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    template_id: Mapped[int] = mapped_column(ForeignKey("onboarding_templates.id", ondelete="CASCADE"), nullable=False, index=True)

    template = relationship("OnboardingTemplate", back_populates="tasks")
    progress_items: Mapped[list["OnboardingTaskProgress"]] = relationship(back_populates="task")


class OnboardingAssignment(TimestampMixin, Base):
    __tablename__ = "onboarding_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default=OnboardingStatus.NOT_STARTED.value, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("onboarding_templates.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    employee = relationship("Employee", back_populates="onboarding_assignments")
    template = relationship("OnboardingTemplate", back_populates="assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    company = relationship("Company", back_populates="onboarding_assignments")
    task_progress: Mapped[list["OnboardingTaskProgress"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )


class OnboardingTaskProgress(TimestampMixin, Base):
    __tablename__ = "onboarding_task_progress"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("onboarding_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("onboarding_tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    assignment = relationship("OnboardingAssignment", back_populates="task_progress")
    task = relationship("OnboardingTask", back_populates="progress_items")
