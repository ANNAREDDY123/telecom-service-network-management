from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.device import DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    imei: str = Field(
        min_length=15,
        max_length=15,
        pattern=r"^\d{15}$",
    )

    device_name: str = Field(
        min_length=2,
        max_length=150,
    )

    manufacturer: str = Field(
        min_length=2,
        max_length=100,
    )

    model_number: str = Field(
        min_length=1,
        max_length=100,
    )

    device_type: DeviceType

    customer_id: int | None = Field(
        default=None,
        gt=0,
    )

    sim_id: int | None = Field(
        default=None,
        gt=0,
    )

    purchase_date: datetime | None = None

    warranty_expiry_date: datetime | None = None


class DeviceUpdate(BaseModel):
    device_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    manufacturer: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    model_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    device_type: DeviceType | None = None

    customer_id: int | None = Field(
        default=None,
        gt=0,
    )

    sim_id: int | None = Field(
        default=None,
        gt=0,
    )

    purchase_date: datetime | None = None

    warranty_expiry_date: datetime | None = None


class DeviceStatusUpdate(BaseModel):
    status: DeviceStatus


class DeviceReplacementCreate(BaseModel):
    new_imei: str = Field(
        min_length=15,
        max_length=15,
        pattern=r"^\d{15}$",
    )

    device_name: str = Field(
        min_length=2,
        max_length=150,
    )

    manufacturer: str = Field(
        min_length=2,
        max_length=100,
    )

    model_number: str = Field(
        min_length=1,
        max_length=100,
    )

    device_type: DeviceType

    reason: str = Field(
        min_length=3,
        max_length=255,
    )

    sim_id: int | None = Field(
        default=None,
        gt=0,
    )


class DeviceResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    imei: str
    device_name: str
    manufacturer: str
    model_number: str
    device_type: DeviceType
    status: DeviceStatus
    customer_id: int | None
    sim_id: int | None
    purchase_date: datetime | None
    activation_date: datetime | None
    warranty_expiry_date: datetime | None
    replacement_of_device_id: int | None
    replacement_reason: str | None
    created_at: datetime
    updated_at: datetime


class DeviceReplacementResponse(BaseModel):
    message: str
    old_device: DeviceResponse
    new_device: DeviceResponse