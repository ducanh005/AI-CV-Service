from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ApplicationStatus
from app.models.mixins import TimestampMixin


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate_application"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        String(20), default=ApplicationStatus.PENDING.value, nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    job = relationship("Job", back_populates="applications")
    candidate = relationship("User", back_populates="applications", foreign_keys=[candidate_id])
    reviewed_by_user = relationship("User", back_populates="reviewed_applications", foreign_keys=[reviewed_by])
    cv = relationship("CV", back_populates="applications")
    ai_score = relationship("AIScore", back_populates="application", uselist=False)
    interviews = relationship("Interview", back_populates="application")
