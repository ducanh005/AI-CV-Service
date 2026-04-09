from pydantic import BaseModel, Field


class DepartmentCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    manager_id: int | None = None


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    manager_id: int | None = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    company_id: int
    manager_id: int | None
    manager_name: str | None = None
    employee_count: int = 0
