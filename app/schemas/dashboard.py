from decimal import Decimal

from pydantic import BaseModel, Field


class TechnicianWorkload(BaseModel):
    technician_id: int
    technician_code: str
    technician_name: str
    status: str
    availability: str
    active_assignments: int
    completed_assignments: int
    total_assignments: int


class TowerStatusSummary(BaseModel):
    status: str
    count: int


class ServiceRequestStatusSummary(BaseModel):
    status: str
    count: int


class PlanUtilization(BaseModel):
    plan_id: int
    plan_code: str
    plan_name: str
    service_type: str
    plan_status: str

    active_subscriptions: int

    data_limit_mb: int | None = None
    data_used_mb: Decimal = Field(default=Decimal("0"))

    utilization_percentage: float | None = None


class DashboardOverviewResponse(BaseModel):
    total_customers: int
    active_customers: int

    active_subscriptions: int
    active_sims: int

    total_data_usage_mb: Decimal

    network_outages: int
    open_tickets: int
    sla_breaches: int

    total_technicians: int
    available_technicians: int
    busy_technicians: int
    technician_workload: list[TechnicianWorkload]

    total_towers: int
    tower_status: list[TowerStatusSummary]

    total_service_requests: int
    service_request_status: list[ServiceRequestStatusSummary]

    plan_utilization: list[PlanUtilization]