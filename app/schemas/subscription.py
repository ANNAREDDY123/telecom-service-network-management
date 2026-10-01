from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import (
    SubscriptionStatus,
    SubscriptionType,
)


class SubscriptionCreate(BaseModel):
    subscription_number: str = Field(
        min_length=5,
        max_length=30,
    )

    subscription_type: SubscriptionType

    customer_id: int = Field(
        gt=0,
    )

    plan_id: int = Field(
        gt=0,
    )

    sim_id: int = Field(
        gt=0,
    )

    device_id: int = Field(
        gt=0,
    )


class SubscriptionUpdate(BaseModel):
    plan_id: int | None = Field(
        default=None,
        gt=0,
    )

    sim_id: int | None = Field(
        default=None,
        gt=0,
    )

    device_id: int | None = Field(
        default=None,
        gt=0,
    )


class SubscriptionStatusUpdate(BaseModel):
    status: SubscriptionStatus


class SubscriptionCancellation(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=255,
    )


class SubscriptionRenewal(BaseModel):
    plan_id: int | None = Field(
        default=None,
        gt=0,
    )


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    subscription_number: str
    subscription_type: SubscriptionType
    status: SubscriptionStatus

    customer_id: int
    plan_id: int
    sim_id: int
    device_id: int

    start_date: date | None
    end_date: date | None

    cancellation_date: date | None
    cancellation_reason: str | None

    renewal_count: int

    created_at: datetime
    updated_at: datetime