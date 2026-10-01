from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class ReportDateFilter(BaseModel):
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "end_date must be greater than or equal to start_date"
            )
        return self


class ReportPagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ReportFilters(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    customer_id: int | None = Field(default=None, gt=0)
    plan_id: int | None = Field(default=None, gt=0)
    subscription_id: int | None = Field(default=None, gt=0)
    tower_id: int | None = Field(default=None, gt=0)
    technician_id: int | None = Field(default=None, gt=0)
    status: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_date_range(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "end_date must be greater than or equal to start_date"
            )
        return self


class CustomerSummaryReport(BaseModel):
    total_customers: int
    active_customers: int
    inactive_customers: int
    verified_kyc_customers: int
    pending_kyc_customers: int
    rejected_kyc_customers: int
    active_subscriptions: int
    active_sims: int


class UsageReportItem(BaseModel):
    customer_id: int
    customer_number: str
    customer_name: str
    subscription_id: int | None = None
    plan_id: int | None = None
    plan_code: str | None = None
    plan_name: str | None = None
    data_used_mb: Decimal


class UsageReportResponse(BaseModel):
    items: list[UsageReportItem]
    total_data_used_mb: Decimal
    total_records: int
    page: int
    page_size: int
    total_pages: int


class OutageReportItem(BaseModel):
    outage_id: int
    outage_number: str | None = None
    tower_id: int | None = None
    tower_code: str | None = None
    status: str
    severity: str | None = None
    started_at: datetime | None = None
    restored_at: datetime | None = None
    duration_minutes: float | None = None


class NetworkReportResponse(BaseModel):
    total_towers: int
    active_towers: int
    maintenance_towers: int
    inactive_towers: int
    total_outages: int
    active_outages: int
    restored_outages: int
    total_outage_duration_minutes: float
    outages: list[OutageReportItem]
    page: int
    page_size: int
    total_pages: int


class SupportReportItem(BaseModel):
    ticket_id: int
    ticket_number: str
    customer_id: int
    category: str
    priority: str
    status: str
    source: str
    created_at: datetime
    resolved_at: datetime | None = None
    resolution_minutes: float | None = None
    sla_status: str | None = None


class SupportReportResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    cancelled_tickets: int
    high_priority_tickets: int
    sla_breaches: int
    response_breaches: int
    resolution_breaches: int
    average_resolution_minutes: float | None = None
    average_response_minutes: float | None = None
    tickets: list[SupportReportItem]
    page: int
    page_size: int
    total_pages: int


class TechnicianReportItem(BaseModel):
    technician_id: int
    technician_code: str
    technician_name: str
    status: str
    availability: str
    total_assignments: int
    active_assignments: int
    completed_assignments: int
    cancelled_assignments: int
    completion_rate: float


class TechnicianReportResponse(BaseModel):
    total_technicians: int
    available_technicians: int
    busy_technicians: int
    total_assignments: int
    completed_assignments: int
    overall_completion_rate: float
    technicians: list[TechnicianReportItem]


class ReportsOverviewResponse(BaseModel):
    report_generated_at: datetime
    customers: CustomerSummaryReport
    total_data_usage_mb: Decimal
    active_subscriptions: int
    active_sims: int
    total_towers: int
    active_outages: int
    total_tickets: int
    open_tickets: int
    sla_breaches: int
    total_service_requests: int
    completed_service_requests: int
    total_technicians: int
    available_technicians: int
    busy_technicians: int