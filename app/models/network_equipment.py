from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.database import Base


class EquipmentType(str, Enum):
    BTS = "BTS"
    ANTENNA = "Antenna"
    ROUTER = "Router"
    SWITCH = "Switch"
    TRANSMISSION = "Transmission"
    POWER_SYSTEM = "Power System"
    OTHER = "Other"


class EquipmentStatus(str, Enum):
    REGISTERED = "Registered"
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    INACTIVE = "Inactive"
    FAILED = "Failed"
    DECOMMISSIONED = "Decommissioned"


class NetworkEquipment(Base):
    __tablename__ = "network_equipment"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    equipment_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    serial_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    equipment_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    equipment_type: Mapped[EquipmentType] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    manufacturer: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[EquipmentStatus] = mapped_column(
        String(30),
        nullable=False,
        default=EquipmentStatus.REGISTERED,
        index=True,
    )

    tower_id: Mapped[int] = mapped_column(
        ForeignKey(
            "network_towers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    installation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    last_maintenance_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    warranty_expiry_date: Mapped[date | None] = mapped_column(
        Date,
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

    tower = relationship(
        "NetworkTower",
        foreign_keys=[tower_id],
    )

    __table_args__ = (
        CheckConstraint(
            "capacity > 0",
            name="ck_equipment_capacity",
        ),
    )

    @validates("equipment_type")
    def validate_equipment_type(
        self,
        key,
        value,
    ):
        if isinstance(value, EquipmentType):
            return value.value

        valid_types = {
            item.value
            for item in EquipmentType
        }

        if value not in valid_types:
            raise ValueError(
                f"Invalid equipment type: {value}"
            )

        return value

    @validates("status")
    def validate_status(
        self,
        key,
        value,
    ):
        if isinstance(value, EquipmentStatus):
            return value.value

        valid_statuses = {
            item.value
            for item in EquipmentStatus
        }

        if value not in valid_statuses:
            raise ValueError(
                f"Invalid equipment status: {value}"
            )

        return value

    @validates("capacity")
    def validate_capacity(
        self,
        key,
        value,
    ):
        if value <= 0:
            raise ValueError(
                "Equipment capacity must be greater than 0"
            )

        return value