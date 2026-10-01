from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SLATrackingStatus(str, Enum):
    ON_TRACK = "On Track"
    RESPONSE_BREACHED = "Response Breached"
    RESOLUTION_BREACHED = "Resolution Breached"
    BOTH_BREACHED = "Both Breached"
    COMPLETED = "Completed"


class SLATracking(Base):
    __tablename__ = "sla_tracking"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    sla_policy_id: Mapped[int] = mapped_column(
        ForeignKey("sla_policies.id"),
        nullable=False,
        index=True,
    )

    response_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    resolution_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    response_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    response_breached: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    resolution_breached: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[SLATrackingStatus] = mapped_column(
        SQLEnum(SLATrackingStatus),
        nullable=False,
        default=SLATrackingStatus.ON_TRACK,
        index=True,
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

    ticket = relationship(
        "SupportTicket",
        back_populates="sla_tracking",
    )

    sla_policy = relationship(
        "SLAPolicy",
        back_populates="tracking_records",
    )