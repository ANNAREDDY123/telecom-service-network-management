from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.support_ticket import (
    TicketCategory,
    TicketPriority,
    TicketSource,
    TicketStatus,
)


class SupportTicketCreate(BaseModel):
    customer_id: int = Field(gt=0)
    outage_id: int | None = Field(default=None, gt=0)

    ticket_number: str = Field(
        min_length=3,
        max_length=50,
    )

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=5,
    )

    category: TicketCategory
    priority: TicketPriority = TicketPriority.MEDIUM
    source: TicketSource = TicketSource.PORTAL


class SupportTicketUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=5,
    )

    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    source: TicketSource | None = None
    outage_id: int | None = Field(
        default=None,
        gt=0,
    )


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketResolution(BaseModel):
    resolution_notes: str = Field(
        min_length=3,
    )


class SupportTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    customer_id: int
    outage_id: int | None

    title: str
    description: str

    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    source: TicketSource

    resolution_notes: str | None
    resolved_at: datetime | None
    closed_at: datetime | None
    cancelled_at: datetime | None

    created_at: datetime
    updated_at: datetime


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketResponse]
    total: int
    page: int
    limit: int
    pages: int