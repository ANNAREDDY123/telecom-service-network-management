from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class OutageType(str, Enum):
    NETWORK = "Network"
    TOWER = "Tower"
    EQUIPMENT = "Equipment"
    POWER = "Power"
    TRANSMISSION = "Transmission"
    MAINTENANCE = "Maintenance"
    OTHER = "Other"


class OutageSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class OutageStatus(str, Enum):
    REPORTED = "Reported"
    INVESTIGATING = "Investigating"
    IDENTIFIED = "Identified"
    IN_PROGRESS = "In Progress"
    RESTORED = "Restored"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class NetworkOutage(Base):
    __tablename__ = "network_outages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    outage_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    outage_type: Mapped[OutageType] = mapped_column(
        nullable=False,
        index=True,
    )

    severity: Mapped[OutageSeverity] = mapped_column(
        nullable=False,
        default=OutageSeverity.MEDIUM,
        index=True,
    )

    status: Mapped[OutageStatus] = mapped_column(
        nullable=False,
        default=OutageStatus.REPORTED,
        index=True,
    )

    tower_id: Mapped[int] = mapped_column(
        ForeignKey("network_towers.id"),
        nullable=False,
        index=True,
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    expected_restore_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    actual_restore_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    affected_customer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tower = relationship(
        "NetworkTower",
        back_populates="outages",
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )

    affected_customers = relationship(
        "OutageAffectedCustomer",
        back_populates="outage",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "affected_customer_count >= 0",
            name="ck_outage_affected_customer_count_nonnegative",
        ),
    )


class OutageAffectedCustomer(Base):
    __tablename__ = "outage_affected_customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    outage_id: Mapped[int] = mapped_column(
        ForeignKey("network_outages.id"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    identified_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    outage = relationship(
        "NetworkOutage",
        back_populates="affected_customers",
    )

    customer = relationship(
        "Customer",
        back_populates="outage_links",
    )

    __table_args__ = (
        UniqueConstraint(
            "outage_id",
            "customer_id",
            name="uq_outage_customer",
        ),
    )