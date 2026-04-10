from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ContractDocumentType, ContractStatus, ContractType


class ContractTargetResponse(BaseModel):
    id: int
    employee_id: int
    full_name: str
    email: str
    source_application_id: int
    accepted_job_id: int
    accepted_job_title: str
    accepted_at: datetime | None = None


class ContractCreateRequest(BaseModel):
    source_application_id: int
    contract_type: ContractType
    start_date: date
    end_date: date | None = None
    salary_amount: int | None = Field(default=None, ge=0)
    salary_currency: str = Field(default="VND", min_length=3, max_length=8)
    benefits: str | None = None
    terms: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ContractCreateRequest":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class ContractUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    contract_type: ContractType | None = None
    start_date: date | None = None
    end_date: date | None = None
    salary_amount: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=8)
    benefits: str | None = None
    terms: str | None = None
    notes: str | None = None


class ContractStatusUpdateRequest(BaseModel):
    status: ContractStatus
    note: str | None = None


class ContractRenewRequest(BaseModel):
    start_date: date
    end_date: date | None = None
    title: str | None = Field(default=None, min_length=2, max_length=160)
    contract_type: ContractType | None = None
    salary_amount: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=8)
    benefits: str | None = None
    terms: str | None = None
    notes: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ContractRenewRequest":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class ContractTerminateRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)
    terminated_at: datetime | None = None


class ContractDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: ContractDocumentType
    file_name: str
    file_path: str
    mime_type: str | None
    notes: str | None
    uploaded_by_id: int | None
    created_at: datetime


class ContractHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: ContractStatus | None
    to_status: ContractStatus
    note: str | None
    changed_at: datetime
    changed_by_id: int | None


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_code: str
    title: str
    employee_id: int
    employee_name: str | None = None
    employee_email: str | None = None
    company_id: int
    source_application_id: int | None
    contract_type: ContractType
    status: ContractStatus
    start_date: date
    end_date: date | None
    signed_at: datetime | None
    salary_amount: int | None
    salary_currency: str
    benefits: str | None
    terms: str | None
    notes: str | None
    termination_reason: str | None
    terminated_at: datetime | None
    version: int
    is_current: bool
    previous_contract_id: int | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime
    days_to_expiry: int | None = None
    expiring_soon: bool = False
    documents: list[ContractDocumentResponse] = Field(default_factory=list)


class ContractDetailResponse(ContractResponse):
    history: list[ContractHistoryResponse] = Field(default_factory=list)
