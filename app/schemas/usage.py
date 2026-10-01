from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.usage import (
    UsageSource,
    UsageStatus,
    UsageType,
)


class UsageCreate(BaseModel):
    subscription_id: int = Field(
        ...,
        gt=0,
    )

    customer_id: int = Field(
        ...,
        gt=0,
    )

    usage_type: UsageType

    usage_date: date | None = None

    data_used_mb: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=3,
    )

    voice_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    sms_count: int | None = Field(
        default=None,
        ge=0,
    )

    source: UsageSource = UsageSource.NETWORK

    reference_id: str | None = Field(
        default=None,
        max_length=100,
    )

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("data_used_mb")
    @classmethod
    def validate_data_usage(cls, value):
        if value is not None and value < 0:
            raise ValueError(
                "Data usage cannot be negative"
            )

        return value

    @field_validator("voice_minutes")
    @classmethod
    def validate_voice_usage(cls, value):
        if value is not None and value < 0:
            raise ValueError(
                "Voice usage cannot be negative"
            )

        return value

    @field_validator("sms_count")
    @classmethod
    def validate_sms_usage(cls, value):
        if value is not None and value < 0:
            raise ValueError(
                "SMS count cannot be negative"
            )

        return value


class UsageUpdate(BaseModel):
    usage_date: date | None = None

    data_used_mb: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=3,
    )

    voice_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    sms_count: int | None = Field(
        default=None,
        ge=0,
    )

    source: UsageSource | None = None

    reference_id: str | None = Field(
        default=None,
        max_length=100,
    )

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )


class UsageStatusUpdate(BaseModel):
    status: UsageStatus


class UsageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    subscription_id: int
    customer_id: int

    usage_type: UsageType
    usage_date: date
    usage_timestamp: datetime

    data_used_mb: Decimal | None
    voice_minutes: int | None
    sms_count: int | None

    status: UsageStatus
    source: UsageSource

    reference_id: str | None
    remarks: str | None

    created_at: datetime
    updated_at: datetime


class UsageSummaryResponse(BaseModel):
    customer_id: int
    subscription_id: int

    period_start: date
    period_end: date

    total_data_used_mb: Decimal
    total_voice_minutes: int
    total_sms_count: int

    data_limit_mb: int | None
    voice_limit_minutes: int | None
    sms_limit: int | None

    remaining_data_mb: Decimal | None
    remaining_voice_minutes: int | None
    remaining_sms: int | None