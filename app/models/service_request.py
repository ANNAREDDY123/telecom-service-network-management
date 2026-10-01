from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ServiceRequestType(str, Enum):
    SIM_REPLACEMENT = "SIM Replacement"
    DEVICE_REPLACEMENT = "Device Replacement"
    PLAN_CHANGE = "Plan Change"
    NEW_SERVICE = "New Service"
    SERVICE_CANCELLATION = "Service Cancellation"
    ADDRESS_CHANGE = "Address Change"
    NUMBER_PORTABILITY = "Number Portability"
    GENERAL = "General"


class ServiceRequestPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ServiceRequestStatus(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    request_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id"),
        nullable=True,
        index=True,
    )

    sim_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("sim_cards.id"),
        nullable=True,
        index=True,
    )

    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id"),
        nullable=True,
        index=True,
    )

    request_type: Mapped[ServiceRequestType] = mapped_column(
        SQLEnum(ServiceRequestType),
        nullable=False,
        index=True,
    )

    priority: Mapped[ServiceRequestPriority] = mapped_column(
        SQLEnum(ServiceRequestPriority),
        nullable=False,
        default=ServiceRequestPriority.MEDIUM,
        index=True,
    )

    status: Mapped[ServiceRequestStatus] = mapped_column(
        SQLEnum(ServiceRequestStatus),
        nullable=False,
        default=ServiceRequestStatus.SUBMITTED,
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

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    processing_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    completed_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
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
        back_populates="service_requests",
    )

    subscription = relationship(
        "Subscription",
    )

    sim_card = relationship(
        "SIMCard",
    )

    device = relationship(
        "Device",
    )