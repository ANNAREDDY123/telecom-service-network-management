from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class AssignmentType(str, Enum):
    SUPPORT_AGENT = "Support Agent"
    FIELD_TECHNICIAN = "Field Technician"


class AssignmentStatus(str, Enum):
    ASSIGNED = "Assigned"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REASSIGNED = "Reassigned"
    UNASSIGNED = "Unassigned"
    CANCELLED = "Cancelled"


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey(
            "support_tickets.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    assigned_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    assignment_type: Mapped[AssignmentType] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    status: Mapped[AssignmentStatus] = mapped_column(
        String(30),
        nullable=False,
        default=AssignmentStatus.ASSIGNED,
        index=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    ticket = relationship(
        "SupportTicket",
        back_populates="assignments",
    )

    assigned_user = relationship(
        "User",
        back_populates="ticket_assignments",
    )