from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.database import Base


class TechnicianStatus(str, Enum):
    AVAILABLE = "Available"
    BUSY = "Busy"
    ON_LEAVE = "On Leave"
    INACTIVE = "Inactive"


class TechnicianAvailability(str, Enum):
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"


class FieldTechnician(Base):
    __tablename__ = "field_technicians"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )

    technician_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    specialization: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    service_area: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[TechnicianStatus] = mapped_column(
        String(30),
        nullable=False,
        default=TechnicianStatus.AVAILABLE,
        index=True,
    )

    availability: Mapped[TechnicianAvailability] = mapped_column(
        String(30),
        nullable=False,
        default=TechnicianAvailability.AVAILABLE,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    joined_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
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

    user = relationship(
        "User",
        back_populates="field_technician",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_field_technician_user",
        ),
    )

    @validates("technician_code")
    def validate_technician_code(self, key, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Technician code cannot be empty"
            )

        return value

    @validates("service_area")
    def validate_service_area(self, key, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Service area cannot be empty"
            )

        return value

    @validates("city")
    def validate_city(self, key, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "City cannot be empty"
            )

        return value

    @validates("state")
    def validate_state(self, key, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "State cannot be empty"
            )

        return value