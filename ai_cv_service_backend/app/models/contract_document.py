from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ContractDocumentType
from app.models.mixins import TimestampMixin


class ContractDocument(TimestampMixin, Base):
    __tablename__ = "contract_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_type: Mapped[ContractDocumentType] = mapped_column(String(32), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)

    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    contract = relationship("Contract", back_populates="documents")
    uploaded_by = relationship("User", back_populates="uploaded_contract_documents")
