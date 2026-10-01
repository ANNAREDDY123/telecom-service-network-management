from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.service_plan import (
    PlanStatus,
    PlanType,
    ServiceType,
)


class ServicePlanCreate(BaseModel):
    plan_code: str = Field(
        min_length=2,
        max_length=50,
    )

    plan_name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    plan_type: PlanType

    service_type: ServiceType

    price: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    validity_days: int = Field(
        gt=0,
        le=3650,
    )

    data_limit_mb: int | None = Field(
        default=None,
        ge=0,
    )

    voice_limit_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    sms_limit: int | None = Field(
        default=None,
        ge=0,
    )


class ServicePlanUpdate(BaseModel):
    plan_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    plan_type: PlanType | None = None

    service_type: ServiceType | None = None

    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    validity_days: int | None = Field(
        default=None,
        gt=0,
        le=3650,
    )

    data_limit_mb: int | None = Field(
        default=None,
        ge=0,
    )

    voice_limit_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    sms_limit: int | None = Field(
        default=None,
        ge=0,
    )


class ServicePlanResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    plan_code: str
    plan_name: str
    description: str | None
    plan_type: PlanType
    service_type: ServiceType
    price: Decimal
    validity_days: int
    data_limit_mb: int | None
    voice_limit_minutes: int | None
    sms_limit: int | None
    status: PlanStatus
    created_at: datetime
    updated_at: datetime


class ServicePlanStatusResponse(BaseModel):
    message: str
    plan: ServicePlanResponse


class ServicePlanComparisonResponse(BaseModel):
    plans: list[ServicePlanResponse]