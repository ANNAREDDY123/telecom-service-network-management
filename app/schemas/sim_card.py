from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.sim_card import SIMStatus, SIMType


class SIMCardCreate(BaseModel):
    sim_number: str = Field(
        min_length=10,
        max_length=30,
    )

    sim_type: SIMType

    customer_id: int | None = Field(
        default=None,
        gt=0,
    )

    plan_id: int | None = Field(
        default=None,
        gt=0,
    )


class SIMCardUpdate(BaseModel):
    sim_type: SIMType | None = None

    customer_id: int | None = Field(
        default=None,
        gt=0,
    )

    plan_id: int | None = Field(
        default=None,
        gt=0,
    )


class SIMStatusUpdate(BaseModel):
    status: SIMStatus


class SIMReplacementCreate(BaseModel):
    new_sim_number: str = Field(
        min_length=10,
        max_length=30,
    )

    sim_type: SIMType

    reason: str = Field(
        min_length=3,
        max_length=255,
    )

    plan_id: int | None = Field(
        default=None,
        gt=0,
    )


class SIMCardResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    sim_number: str
    sim_type: SIMType
    status: SIMStatus
    activation_date: date | None
    customer_id: int | None
    plan_id: int | None
    replacement_of_sim_id: int | None
    replacement_reason: str | None
    created_at: datetime
    updated_at: datetime


class SIMReplacementResponse(BaseModel):
    message: str
    old_sim: SIMCardResponse
    new_sim: SIMCardResponse