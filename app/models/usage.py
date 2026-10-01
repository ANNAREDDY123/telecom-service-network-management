from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.database import Base


class UsageType(str, Enum):
    DATA = "Data"
    VOICE = "Voice"
    SMS = "SMS"


class UsageStatus(str, Enum):
    RECORDED = "Recorded"
    PROCESSED = "Processed"
    REVERSED = "Reversed"


class UsageSource(str, Enum):
    NETWORK = "Network"
    MANUAL = "Manual"
    IMPORT = "Import"
    SYSTEM = "System"


class Usage(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey(
            "subscriptions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    usage_type: Mapped[UsageType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    usage_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        index=True,
    )

    usage_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Data usage in MB
    data_used_mb: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        default=None,
    )

    # Voice usage in minutes
    voice_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    # Number of SMS messages
    sms_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    status: Mapped[UsageStatus] = mapped_column(
        String(20),
        nullable=False,
        default=UsageStatus.RECORDED,
        index=True,
    )

    source: Mapped[UsageSource] = mapped_column(
        String(20),
        nullable=False,
        default=UsageSource.NETWORK,
        index=True,
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
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

    # Relationships
    subscription = relationship(
        "Subscription",
        foreign_keys=[subscription_id],
    )

    customer = relationship(
        "Customer",
        foreign_keys=[customer_id],
    )

    __table_args__ = (
        CheckConstraint(
            "data_used_mb IS NULL OR data_used_mb >= 0",
            name="ck_usage_data_non_negative",
        ),
        CheckConstraint(
            "voice_minutes IS NULL OR voice_minutes >= 0",
            name="ck_usage_voice_non_negative",
        ),
        CheckConstraint(
            "sms_count IS NULL OR sms_count >= 0",
            name="ck_usage_sms_non_negative",
        ),
    )

    @validates("usage_type")
    def validate_usage_type(
        self,
        key,
        value,
    ):
        if isinstance(value, UsageType):
            return value.value

        valid_types = {
            item.value
            for item in UsageType
        }

        if value not in valid_types:
            raise ValueError(
                f"Invalid usage type: {value}"
            )

        return value

    @validates("status")
    def validate_status(
        self,
        key,
        value,
    ):
        if isinstance(value, UsageStatus):
            return value.value

        valid_statuses = {
            item.value
            for item in UsageStatus
        }

        if value not in valid_statuses:
            raise ValueError(
                f"Invalid usage status: {value}"
            )

        return value

    @validates("source")
    def validate_source(
        self,
        key,
        value,
    ):
        if isinstance(value, UsageSource):
            return value.value

        valid_sources = {
            item.value
            for item in UsageSource
        }

        if value not in valid_sources:
            raise ValueError(
                f"Invalid usage source: {value}"
            )

        return value

    @validates("data_used_mb")
    def validate_data_usage(
        self,
        key,
        value,
    ):
        if value is not None:
            value = Decimal(str(value))

            if value < 0:
                raise ValueError(
                    "Data usage cannot be negative"
                )

        return value

    @validates("voice_minutes")
    def validate_voice_usage(
        self,
        key,
        value,
    ):
        if value is not None:
            if value < 0:
                raise ValueError(
                    "Voice usage cannot be negative"
                )

        return value

    @validates("sms_count")
    def validate_sms_usage(
        self,
        key,
        value,
    ):
        if value is not None:
            if value < 0:
                raise ValueError(
                    "SMS count cannot be negative"
                )

        return value