from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket_assignment import (
    AssignmentStatus,
    AssignmentType,
)


class TicketAssignmentCreate(BaseModel):
    ticket_id: int = Field(gt=0)
    assigned_user_id: int = Field(gt=0)
    assignment_type: AssignmentType
    notes: str | None = Field(default=None, max_length=2000)


class TicketAssignmentUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class AssignmentStatusUpdate(BaseModel):
    status: AssignmentStatus


class TicketAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    assigned_user_id: int
    assignment_type: AssignmentType
    status: AssignmentStatus
    assigned_at: datetime
    accepted_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    unassigned_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TicketAssignmentListResponse(BaseModel):
    items: list[TicketAssignmentResponse]
    total: int
    page: int
    limit: int
    pages: int