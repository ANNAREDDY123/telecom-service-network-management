from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.sla_policy import SLAPriority, SLAStatus
from app.models.sla_tracking import SLATrackingStatus


class SLAPolicyCreate(BaseModel):
    sla_code: str = Field(..., min_length=2, max_length=50)
    sla_name: str = Field(..., min_length=2, max_length=150)
    priority: SLAPriority
    response_time_minutes: int = Field(..., gt=0)
    resolution_time_minutes: int = Field(..., gt=0)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("sla_code", "sla_name")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class SLAPolicyUpdate(BaseModel):
    sla_name: str | None = Field(default=None, min_length=2, max_length=150)
    response_time_minutes: int | None = Field(default=None, gt=0)
    resolution_time_minutes: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("sla_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("SLA name cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class SLAStatusUpdate(BaseModel):
    status: SLAStatus


class SLAPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sla_code: str
    sla_name: str
    priority: SLAPriority
    response_time_minutes: int
    resolution_time_minutes: int
    status: SLAStatus
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SLAPolicyListResponse(BaseModel):
    items: list[SLAPolicyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SLATrackingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    sla_policy_id: int
    response_deadline: datetime
    resolution_deadline: datetime
    response_at: datetime | None
    resolved_at: datetime | None
    response_breached: bool
    resolution_breached: bool
    status: SLATrackingStatus
    created_at: datetime
    updated_at: datetime


class SLATrackingListResponse(BaseModel):
    items: list[SLATrackingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SLABreachCheckResponse(BaseModel):
    ticket_id: int
    response_breached: bool
    resolution_breached: bool
    status: SLATrackingStatus
    response_deadline: datetime
    resolution_deadline: datetime
    response_at: datetime | None
    resolved_at: datetime | None


class SLAResponseUpdate(BaseModel):
    response_at: datetime | None = None


class SLAResolutionUpdate(BaseModel):
    resolved_at: datetime | None = None