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


class SIMType(str, Enum):
    PHYSICAL = "Physical"
    ESIM = "eSIM"


class SIMStatus(str, Enum):
    AVAILABLE = "Available"
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    LOST = "Lost"
    BLOCKED = "Blocked"
    DEACTIVATED = "Deactivated"


class SIMCard(Base):
    __tablename__ = "sim_cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    sim_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    sim_type: Mapped[SIMType] = mapped_column(
        SQLEnum(SIMType),
        nullable=False,
        index=True,
    )

    status: Mapped[SIMStatus] = mapped_column(
        SQLEnum(SIMStatus),
        nullable=False,
        default=SIMStatus.AVAILABLE,
        index=True,
    )

    activation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True,
        index=True,
    )

    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_plans.id"),
        nullable=True,
        index=True,
    )

    replacement_of_sim_id: Mapped[int | None] = mapped_column(
        ForeignKey("sim_cards.id"),
        nullable=True,
        index=True,
    )

    replacement_reason: Mapped[str | None] = mapped_column(
        String(255),
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
        foreign_keys=[customer_id],
        backref="sim_cards",
    )

    plan = relationship(
        "ServicePlan",
        foreign_keys=[plan_id],
        backref="sim_cards",
    )

    replacement_of = relationship(
        "SIMCard",
        remote_side=[id],
        foreign_keys=[replacement_of_sim_id],
    )