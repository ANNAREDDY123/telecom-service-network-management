from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.customer import KYCStatus


class CustomerCreate(BaseModel):
    user_id: int

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: str = Field(
        min_length=5,
        max_length=255,
    )

    phone: str = Field(
        min_length=7,
        max_length=20,
    )

    alternate_phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    email: str | None = Field(
        default=None,
        min_length=5,
        max_length=255,
    )

    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )

    alternate_phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )


class CustomerKYCUpdate(BaseModel):
    kyc_status: KYCStatus


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    customer_number: str
    full_name: str
    email: str
    phone: str
    alternate_phone: str | None
    kyc_status: KYCStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerAddressCreate(BaseModel):
    address_line1: str = Field(
        min_length=3,
        max_length=255,
    )

    address_line2: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str = Field(
        min_length=2,
        max_length=100,
    )

    state: str = Field(
        min_length=2,
        max_length=100,
    )

    postal_code: str = Field(
        min_length=3,
        max_length=20,
    )

    country: str = Field(
        default="India",
        min_length=2,
        max_length=100,
    )

    address_type: str = Field(
        default="Residential",
        max_length=30,
    )

    is_primary: bool = False


class CustomerAddressUpdate(BaseModel):
    address_line1: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    address_line2: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    postal_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=20,
    )

    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    address_type: str | None = Field(
        default=None,
        max_length=30,
    )

    is_primary: bool | None = None


class CustomerAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class CustomerHistoryResponse(BaseModel):
    customer_id: int
    customer_number: str
    customer_name: str
    account_status: str
    kyc_status: KYCStatus
    created_at: datetime
    updated_at: datetime
    address_count: int