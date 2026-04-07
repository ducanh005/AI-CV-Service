from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ScoringJob(TimestampMixin, Base):
    __tablename__ = "scoring_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    source_job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    min_score: Mapped[float] = mapped_column(Float, nullable=False, default=60.0)
    notify_candidates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criteria_json: Mapped[dict | None] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submitted_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)

    source_job = relationship("Job")
    requester = relationship("User")
    items = relationship("ScoringJobItem", back_populates="scoring_job", cascade="all, delete-orphan")
