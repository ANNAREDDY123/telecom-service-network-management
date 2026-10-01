from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.field_technician import (
    TechnicianAvailability,
    TechnicianStatus,
)


class FieldTechnicianCreate(BaseModel):
    user_id: int = Field(gt=0)
    technician_code: str = Field(
        min_length=2,
        max_length=50,
    )
    specialization: str | None = Field(
        default=None,
        max_length=150,
    )
    skills: str | None = None
    service_area: str = Field(
        min_length=2,
        max_length=200,
    )
    city: str = Field(
        min_length=2,
        max_length=100,
    )
    state: str = Field(
        min_length=2,
        max_length=100,
    )
    status: TechnicianStatus = (
        TechnicianStatus.AVAILABLE
    )
    availability: TechnicianAvailability = (
        TechnicianAvailability.AVAILABLE
    )
    joined_date: datetime | None = None
    notes: str | None = None


class FieldTechnicianUpdate(BaseModel):
    specialization: str | None = Field(
        default=None,
        max_length=150,
    )
    skills: str | None = None
    service_area: str | None = Field(
        default=None,
        max_length=200,
    )
    city: str | None = Field(
        default=None,
        max_length=100,
    )
    state: str | None = Field(
        default=None,
        max_length=100,
    )
    status: TechnicianStatus | None = None
    availability: TechnicianAvailability | None = None
    joined_date: datetime | None = None
    notes: str | None = None


class TechnicianStatusUpdate(BaseModel):
    status: TechnicianStatus


class TechnicianAvailabilityUpdate(BaseModel):
    availability: TechnicianAvailability


class FieldTechnicianResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    technician_code: str
    specialization: str | None
    skills: str | None
    service_area: str
    city: str
    state: str
    status: TechnicianStatus
    availability: TechnicianAvailability
    is_active: bool
    joined_date: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class FieldTechnicianListResponse(BaseModel):
    items: list[FieldTechnicianResponse]
    total: int
    page: int
    limit: int
    pages: int