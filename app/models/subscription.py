from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SubscriptionType(str, Enum):
    PREPAID = "Prepaid"
    POSTPAID = "Postpaid"


class SubscriptionStatus(str, Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    EXPIRED = "Expired"
    CANCELLED = "Cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    subscription_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    subscription_type: Mapped[SubscriptionType] = mapped_column(
        SQLEnum(SubscriptionType),
        nullable=False,
        index=True,
    )

    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        nullable=False,
        default=SubscriptionStatus.PENDING,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("service_plans.id"),
        nullable=False,
        index=True,
    )

    sim_id: Mapped[int] = mapped_column(
        ForeignKey("sim_cards.id"),
        nullable=False,
        index=True,
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
        index=True,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    cancellation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    renewal_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
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
        foreign_keys=[customer_id],
        backref="subscriptions",
    )

    plan = relationship(
        "ServicePlan",
        foreign_keys=[plan_id],
        backref="subscriptions",
    )

    sim = relationship(
        "SIMCard",
        foreign_keys=[sim_id],
        backref="subscriptions",
    )

    device = relationship(
        "Device",
        foreign_keys=[device_id],
        backref="subscriptions",
    )