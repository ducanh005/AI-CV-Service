from datetime import date

from pydantic import BaseModel, Field

from app.models.enums import ContractType, EmployeeStatus


class EmployeeCreateRequest(BaseModel):
    user_id: int
    department_id: int
    employee_code: str = Field(min_length=1, max_length=50)
    position: str = Field(min_length=2, max_length=150)
    contract_type: ContractType = ContractType.PERMANENT
    start_date: date
    end_date: date | None = None
    identity_number: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class EmployeeUpdateRequest(BaseModel):
    department_id: int | None = None
    position: str | None = Field(default=None, min_length=2, max_length=150)
    status: EmployeeStatus | None = None
    contract_type: ContractType | None = None
    start_date: date | None = None
    end_date: date | None = None
    identity_number: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    position: str
    status: str
    contract_type: str
    start_date: date
    end_date: date | None
    identity_number: str | None
    notes: str | None
    user_id: int
    department_id: int
    company_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    department_name: str | None = None
