from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ContractStatus


class ContractStatusHistory(Base):
    __tablename__ = "contract_status_histories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    from_status: Mapped[ContractStatus | None] = mapped_column(String(20), index=True)
    to_status: Mapped[ContractStatus] = mapped_column(String(20), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    contract = relationship("Contract", back_populates="status_history")
    changed_by = relationship("User", back_populates="contract_status_changes")
