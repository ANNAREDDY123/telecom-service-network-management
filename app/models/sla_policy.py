from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SLAPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SLAStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class SLAPolicy(Base):
    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    sla_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    sla_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    priority: Mapped[SLAPriority] = mapped_column(
        SQLEnum(SLAPriority),
        nullable=False,
        index=True,
    )

    response_time_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    resolution_time_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[SLAStatus] = mapped_column(
        SQLEnum(SLAStatus),
        nullable=False,
        default=SLAStatus.ACTIVE,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    tracking_records = relationship(
        "SLATracking",
        back_populates="sla_policy",
    )