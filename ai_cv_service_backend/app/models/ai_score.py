from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class AIScore(TimestampMixin, Base):
    __tablename__ = "ai_scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    reasoning: Mapped[str | None] = mapped_column(Text)

    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False)

    application = relationship("Application", back_populates="ai_score")
