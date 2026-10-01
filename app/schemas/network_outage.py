from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.network_outage import (
    OutageSeverity,
    OutageStatus,
    OutageType,
)


class OutageCreate(BaseModel):
    outage_number: str = Field(
        min_length=3,
        max_length=50,
    )

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str | None = None

    outage_type: OutageType

    severity: OutageSeverity = OutageSeverity.MEDIUM

    tower_id: int = Field(gt=0)

    start_time: datetime

    expected_restore_time: datetime | None = None

    root_cause: str | None = None

    @model_validator(mode="after")
    def validate_times(self):
        if (
            self.expected_restore_time is not None
            and self.expected_restore_time < self.start_time
        ):
            raise ValueError(
                "Expected restore time cannot be before outage start time."
            )

        return self


class OutageUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = None

    outage_type: OutageType | None = None

    severity: OutageSeverity | None = None

    expected_restore_time: datetime | None = None

    root_cause: str | None = None

    resolution_notes: str | None = None


class OutageStatusUpdate(BaseModel):
    status: OutageStatus


class OutageRestore(BaseModel):
    actual_restore_time: datetime | None = None

    resolution_notes: str = Field(
        min_length=3,
    )


class AffectedCustomersCreate(BaseModel):
    customer_ids: list[int] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_unique_customers(self):
        if len(self.customer_ids) != len(
            set(self.customer_ids)
        ):
            raise ValueError(
                "Duplicate customer IDs are not allowed."
            )

        return self


class AffectedCustomerResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    outage_id: int
    customer_id: int
    identified_at: datetime
    resolved_at: datetime | None
    created_at: datetime


class OutageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    outage_number: str
    title: str
    description: str | None

    outage_type: OutageType
    severity: OutageSeverity
    status: OutageStatus

    tower_id: int

    start_time: datetime
    expected_restore_time: datetime | None
    actual_restore_time: datetime | None

    root_cause: str | None
    resolution_notes: str | None

    affected_customer_count: int

    created_by: int | None

    created_at: datetime
    updated_at: datetime


class OutageListResponse(BaseModel):
    items: list[OutageResponse]
    total: int
    page: int
    page_size: int


class AffectedCustomerListResponse(BaseModel):
    items: list[AffectedCustomerResponse]
    total: int


class OutageSummaryResponse(BaseModel):
    outage_id: int
    outage_number: str
    status: OutageStatus
    severity: OutageSeverity
    affected_customer_count: int
    start_time: datetime
    expected_restore_time: datetime | None
    actual_restore_time: datetime | None
    duration_minutes: int | None