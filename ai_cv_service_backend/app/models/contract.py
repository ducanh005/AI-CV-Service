from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ContractStatus, ContractType
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Contract(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contract_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    contract_type: Mapped[ContractType] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[ContractStatus] = mapped_column(
        String(20), default=ContractStatus.DRAFT.value, nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date | None] = mapped_column(Date, index=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    salary_amount: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(8), default="VND", nullable=False)
    benefits: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    termination_reason: Mapped[str | None] = mapped_column(Text)
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    source_application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    previous_contract_id: Mapped[int | None] = mapped_column(
        ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    employee = relationship("User", back_populates="contracts_as_employee", foreign_keys=[employee_id])
    company = relationship("Company", back_populates="contracts")
    source_application = relationship("Application", back_populates="contracts")
    created_by = relationship("User", back_populates="created_contracts", foreign_keys=[created_by_id])
    previous_contract = relationship(
        "Contract",
        remote_side=[id],
        back_populates="renewed_contracts",
        foreign_keys=[previous_contract_id],
    )
    renewed_contracts = relationship("Contract", back_populates="previous_contract")
    documents = relationship("ContractDocument", back_populates="contract", cascade="all, delete-orphan")
    status_history = relationship("ContractStatusHistory", back_populates="contract", cascade="all, delete-orphan")
