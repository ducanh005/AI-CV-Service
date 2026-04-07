from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScoringJobItem(Base):
    __tablename__ = "scoring_job_items"
    __table_args__ = (UniqueConstraint("scoring_job_id", "application_id", name="uq_scoring_job_application"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scoring_job_id: Mapped[str] = mapped_column(ForeignKey("scoring_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)

    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)

    score: Mapped[float | None] = mapped_column(Float)
    reasoning: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)

    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    scoring_job = relationship("ScoringJob", back_populates="items")
    application = relationship("Application")
