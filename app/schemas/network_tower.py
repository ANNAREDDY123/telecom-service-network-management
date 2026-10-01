from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.network_tower import (
    TowerStatus,
    TowerType,
)


class NetworkTowerCreate(BaseModel):
    tower_code: str = Field(
        ...,
        min_length=2,
        max_length=50,
    )

    tower_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    tower_type: TowerType

    latitude: Decimal = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: Decimal = Field(
        ...,
        ge=-180,
        le=180,
    )

    address: str = Field(
        ...,
        min_length=3,
        max_length=300,
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    postal_code: str = Field(
        ...,
        min_length=3,
        max_length=20,
    )

    coverage_radius_km: Decimal = Field(
        ...,
        gt=0,
    )

    capacity: int = Field(
        ...,
        gt=0,
    )

    installation_date: date | None = None

    @field_validator("tower_code")
    @classmethod
    def validate_tower_code(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Tower code cannot be empty"
            )

        return value

    @field_validator("tower_name")
    @classmethod
    def validate_tower_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Tower name cannot be empty"
            )

        return value


class NetworkTowerUpdate(BaseModel):
    tower_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    tower_type: TowerType | None = None

    latitude: Decimal | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    address: str | None = Field(
        default=None,
        min_length=3,
        max_length=300,
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

    coverage_radius_km: Decimal | None = Field(
        default=None,
        gt=0,
    )

    capacity: int | None = Field(
        default=None,
        gt=0,
    )

    installation_date: date | None = None


class NetworkTowerStatusUpdate(BaseModel):
    status: TowerStatus


class NetworkTowerResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    tower_code: str
    tower_name: str
    tower_type: TowerType
    status: TowerStatus
    latitude: Decimal
    longitude: Decimal
    address: str
    city: str
    state: str
    postal_code: str
    coverage_radius_km: Decimal
    capacity: int
    installation_date: date | None
    last_maintenance_date: date | None
    created_at: datetime
    updated_at: datetime