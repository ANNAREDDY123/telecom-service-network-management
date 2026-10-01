from datetime import datetime, timezone
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


class DeviceType(str, Enum):
    SMARTPHONE = "Smartphone"
    FEATURE_PHONE = "Feature Phone"
    TABLET = "Tablet"
    ROUTER = "Router"
    MODEM = "Modem"
    OTHER = "Other"


class DeviceStatus(str, Enum):
    REGISTERED = "Registered"
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    LOST = "Lost"
    BLOCKED = "Blocked"
    DEACTIVATED = "Deactivated"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    imei: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
        index=True,
    )

    device_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    manufacturer: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    device_type: Mapped[DeviceType] = mapped_column(
        SQLEnum(DeviceType),
        nullable=False,
        index=True,
    )

    status: Mapped[DeviceStatus] = mapped_column(
        SQLEnum(DeviceStatus),
        nullable=False,
        default=DeviceStatus.REGISTERED,
        index=True,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True,
        index=True,
    )

    sim_id: Mapped[int | None] = mapped_column(
        ForeignKey("sim_cards.id"),
        nullable=True,
        index=True,
    )

    purchase_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    activation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    warranty_expiry_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    replacement_of_device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id"),
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
        backref="devices",
    )

    sim = relationship(
        "SIMCard",
        foreign_keys=[sim_id],
        backref="device",
    )

    replacement_of = relationship(
        "Device",
        remote_side=[id],
        foreign_keys=[replacement_of_device_id],
    )