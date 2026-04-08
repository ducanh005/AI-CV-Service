from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.enums import InterviewMode, InterviewResultStatus


class Interview(TimestampMixin, Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Interview")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    interview_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="online",
        index=True,
    )
    location: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    result_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduled",
        index=True,
    )
    
    calendar_event_id: Mapped[str | None] = mapped_column(String(255), index=True)
    calendar_url: Mapped[str | None] = mapped_column(String(500))
    meeting_link: Mapped[str | None] = mapped_column(String(255))

    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hr_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    application = relationship("Application", back_populates="interviews")
    candidate = relationship("User", back_populates="interviews_as_candidate", foreign_keys=[candidate_id])
    hr = relationship("User", back_populates="interviews_as_hr", foreign_keys=[hr_id])
