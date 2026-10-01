from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class NotificationType(str, Enum):
    TICKET_CREATED = "Ticket Created"
    TICKET_ASSIGNED = "Ticket Assigned"
    TICKET_STATUS_CHANGED = "Ticket Status Changed"

    SLA_RESPONSE_BREACH = "SLA Response Breach"
    SLA_RESOLUTION_BREACH = "SLA Resolution Breach"

    NETWORK_OUTAGE_STARTED = "Network Outage Started"
    NETWORK_OUTAGE_RESTORED = "Network Outage Restored"

    SERVICE_REQUEST_SUBMITTED = "Service Request Submitted"
    SERVICE_REQUEST_APPROVED = "Service Request Approved"
    SERVICE_REQUEST_REJECTED = "Service Request Rejected"
    SERVICE_REQUEST_COMPLETED = "Service Request Completed"

    SUBSCRIPTION_ACTIVATED = "Subscription Activated"
    SUBSCRIPTION_CANCELLED = "Subscription Cancelled"

    GENERAL = "General"


class NotificationChannel(str, Enum):
    IN_APP = "In App"
    EMAIL = "Email"
    SMS = "SMS"


class NotificationPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class NotificationStatus(str, Enum):
    PENDING = "Pending"
    SENT = "Sent"
    FAILED = "Failed"
    READ = "Read"
    EXPIRED = "Expired"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType),
        nullable=False,
        index=True,
    )

    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel),
        nullable=False,
        default=NotificationChannel.IN_APP,
        index=True,
    )

    priority: Mapped[NotificationPriority] = mapped_column(
        SQLEnum(NotificationPriority),
        nullable=False,
        default=NotificationPriority.MEDIUM,
        index=True,
    )

    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    reference_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    event_key: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        unique=True,
        index=True,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
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

    user = relationship(
        "User",
        back_populates="notifications",
    )