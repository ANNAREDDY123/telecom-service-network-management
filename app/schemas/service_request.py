from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.service_request import (
    ServiceRequestPriority,
    ServiceRequestStatus,
    ServiceRequestType,
)


class ServiceRequestCreate(BaseModel):
    request_number: str = Field(min_length=3, max_length=50)
    customer_id: int
    subscription_id: int | None = None
    sim_card_id: int | None = None
    device_id: int | None = None
    request_type: ServiceRequestType
    priority: ServiceRequestPriority = ServiceRequestPriority.MEDIUM
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)

    @field_validator("request_number", "title", "description")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty")

        return value


class ServiceRequestUpdate(BaseModel):
    priority: ServiceRequestPriority | None = None
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=5)
    processing_notes: str | None = None

    @field_validator(
        "title",
        "description",
        "processing_notes",
    )
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty")

        return value


class ServiceRequestStatusUpdate(BaseModel):
    status: ServiceRequestStatus
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Notes cannot be empty")

        return value


class ServiceRequestRejection(BaseModel):
    rejection_reason: str = Field(min_length=3)

    @field_validator("rejection_reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Rejection reason cannot be empty")

        return value


class ServiceRequestCompletion(BaseModel):
    completed_notes: str | None = None

    @field_validator("completed_notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Completion notes cannot be empty")

        return value


class ServiceRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_number: str
    customer_id: int
    subscription_id: int | None
    sim_card_id: int | None
    device_id: int | None
    request_type: ServiceRequestType
    priority: ServiceRequestPriority
    status: ServiceRequestStatus
    title: str
    description: str
    rejection_reason: str | None
    processing_notes: str | None
    completed_notes: str | None
    submitted_at: datetime
    reviewed_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ServiceRequestListResponse(BaseModel):
    items: list[ServiceRequestResponse]
    total: int
    page: int
    page_size: int
    pages: int