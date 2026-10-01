from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.database import Base


class TowerType(str, Enum):
    MACRO = "Macro"
    MICRO = "Micro"
    SMALL_CELL = "Small Cell"
    INDOOR = "Indoor"


class TowerStatus(str, Enum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    INACTIVE = "Inactive"
    DECOMMISSIONED = "Decommissioned"


class NetworkTower(Base):
    __tablename__ = "network_towers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tower_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    tower_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    tower_type: Mapped[TowerType] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    status: Mapped[TowerStatus] = mapped_column(
        String(30),
        nullable=False,
        default=TowerStatus.PLANNED,
        index=True,
    )

    latitude: Mapped[Decimal] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    longitude: Mapped[Decimal] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    coverage_radius_km: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
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

    outages = relationship(
        "NetworkOutage",
        back_populates="tower",
    )

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_tower_latitude",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_tower_longitude",
        ),
        CheckConstraint(
            "coverage_radius_km > 0",
            name="ck_tower_coverage_radius",
        ),
        CheckConstraint(
            "capacity > 0",
            name="ck_tower_capacity",
        ),
    )

    @validates("tower_type")
    def validate_tower_type(self, key, value):
        if isinstance(value, TowerType):
            return value.value

        valid_types = {
            item.value for item in TowerType
        }

        if value not in valid_types:
            raise ValueError(
                f"Invalid tower type: {value}"
            )

        return value

    @validates("status")
    def validate_status(self, key, value):
        if isinstance(value, TowerStatus):
            return value.value

        valid_statuses = {
            item.value for item in TowerStatus
        }

        if value not in valid_statuses:
            raise ValueError(
                f"Invalid tower status: {value}"
            )

        return value

    @validates("latitude")
    def validate_latitude(self, key, value):
        value = Decimal(str(value))

        if value < -90 or value > 90:
            raise ValueError(
                "Latitude must be between -90 and 90"
            )

        return value

    @validates("longitude")
    def validate_longitude(self, key, value):
        value = Decimal(str(value))

        if value < -180 or value > 180:
            raise ValueError(
                "Longitude must be between -180 and 180"
            )

        return value

    @validates("coverage_radius_km")
    def validate_coverage_radius(self, key, value):
        value = Decimal(str(value))

        if value <= 0:
            raise ValueError(
                "Coverage radius must be greater than 0"
            )

        return value

    @validates("capacity")
    def validate_capacity(self, key, value):
        if value <= 0:
            raise ValueError(
                "Tower capacity must be greater than 0"
            )

        return value