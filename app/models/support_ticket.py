from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TicketCategory(str, Enum):
    NETWORK = "Network"
    BILLING = "Billing"
    TECHNICAL = "Technical"
    SIM = "SIM"
    DEVICE = "Device"
    SERVICE = "Service"
    ACCOUNT = "Account"
    OTHER = "Other"


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    PENDING_CUSTOMER = "Pending Customer"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class TicketSource(str, Enum):
    PORTAL = "Portal"
    PHONE = "Phone"
    EMAIL = "Email"
    SYSTEM = "System"
    FIELD = "Field"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    ticket_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    outage_id: Mapped[int | None] = mapped_column(
        ForeignKey("network_outages.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[TicketCategory] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    priority: Mapped[TicketPriority] = mapped_column(
        String(20),
        nullable=False,
        default=TicketPriority.MEDIUM,
        index=True,
    )

    status: Mapped[TicketStatus] = mapped_column(
        String(30),
        nullable=False,
        default=TicketStatus.OPEN,
        index=True,
    )

    source: Mapped[TicketSource] = mapped_column(
        String(20),
        nullable=False,
        default=TicketSource.PORTAL,
        index=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    customer = relationship(
        "Customer",
        back_populates="support_tickets",
    )

    outage = relationship(
        "NetworkOutage",
    )

    assignments = relationship(
        "TicketAssignment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    sla_tracking = relationship(
        "SLATracking",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan",
    )