from pydantic import BaseModel, Field


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    website: str | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)


class CompanyUpdateRequest(BaseModel):
    website: str | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)


class CompanyResponse(BaseModel):
    id: int
    name: str
    website: str | None
    description: str | None
    location: str | None
