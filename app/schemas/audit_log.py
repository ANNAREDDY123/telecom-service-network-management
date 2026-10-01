from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    action: str
    resource: str
    resource_id: int | None = None
    method: str
    endpoint: str
    status_code: int
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    details: str | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogCreate(BaseModel):
    user_id: int | None = Field(default=None, gt=0)
    action: str = Field(min_length=1, max_length=30)
    resource: str = Field(min_length=1, max_length=100)
    resource_id: int | None = Field(default=None, gt=0)
    method: str = Field(min_length=1, max_length=10)
    endpoint: str = Field(min_length=1, max_length=500)
    status_code: int = Field(ge=100, le=599)
    ip_address: str | None = Field(default=None, max_length=100)
    user_agent: str | None = Field(default=None, max_length=500)
    request_id: str | None = Field(default=None, max_length=100)
    details: str | None = None