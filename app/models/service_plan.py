from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PlanType(str, Enum):
    PREPAID = "Prepaid"
    POSTPAID = "Postpaid"


class ServiceType(str, Enum):
    DATA = "Data"
    VOICE = "Voice"
    SMS = "SMS"


class PlanStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class ServicePlan(Base):
    __tablename__ = "service_plans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    plan_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    plan_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    plan_type: Mapped[PlanType] = mapped_column(
        SQLEnum(PlanType),
        nullable=False,
        index=True,
    )

    service_type: Mapped[ServiceType] = mapped_column(
        SQLEnum(ServiceType),
        nullable=False,
        index=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    validity_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    data_limit_mb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    voice_limit_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    sms_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[PlanStatus] = mapped_column(
        SQLEnum(PlanStatus),
        nullable=False,
        default=PlanStatus.ACTIVE,
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