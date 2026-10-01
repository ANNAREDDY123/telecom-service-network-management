from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.network_equipment import (
    EquipmentStatus,
    EquipmentType,
)


class NetworkEquipmentCreate(BaseModel):
    equipment_code: str = Field(
        ...,
        min_length=2,
        max_length=50,
    )

    serial_number: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    equipment_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    equipment_type: EquipmentType

    manufacturer: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    model_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    tower_id: int = Field(
        ...,
        gt=0,
    )

    capacity: int = Field(
        ...,
        gt=0,
    )

    installation_date: date | None = None

    warranty_expiry_date: date | None = None

    @field_validator(
        "equipment_code",
        "serial_number",
        "equipment_name",
        "manufacturer",
        "model_number",
    )
    @classmethod
    def validate_text_fields(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Field cannot be empty"
            )

        return value


class NetworkEquipmentUpdate(BaseModel):
    equipment_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    equipment_type: EquipmentType | None = None

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

    tower_id: int | None = Field(
        default=None,
        gt=0,
    )

    capacity: int | None = Field(
        default=None,
        gt=0,
    )

    installation_date: date | None = None

    warranty_expiry_date: date | None = None


class NetworkEquipmentStatusUpdate(BaseModel):
    status: EquipmentStatus


class NetworkEquipmentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    equipment_code: str
    serial_number: str
    equipment_name: str
    equipment_type: EquipmentType
    manufacturer: str
    model_number: str
    status: EquipmentStatus
    tower_id: int
    capacity: int
    installation_date: date | None
    last_maintenance_date: date | None
    warranty_expiry_date: date | None
    created_at: datetime
    updated_at: datetime