from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int


class TimestampResponse(ORMBaseModel):
    created_at: datetime
    updated_at: datetime
