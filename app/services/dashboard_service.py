from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import (
    DashboardRepository,
)


class DashboardService:

    @staticmethod
    def get_overview(db: Session) -> dict:
        repository = DashboardRepository(db)

        return {
            "total_customers": (
                repository.get_total_customers()
            ),
            "active_customers": (
                repository.get_active_customers()
            ),
            "active_subscriptions": (
                repository.get_active_subscriptions()
            ),
            "active_sims": (
                repository.get_active_sims()
            ),
            "total_data_usage_mb": (
                repository.get_total_data_usage_mb()
            ),
            "network_outages": (
                repository.get_network_outages()
            ),
            "open_tickets": (
                repository.get_open_tickets()
            ),
            "sla_breaches": (
                repository.get_sla_breaches()
            ),
            "total_technicians": (
                repository.get_total_technicians()
            ),
            "available_technicians": (
                repository.get_available_technicians()
            ),
            "busy_technicians": (
                repository.get_busy_technicians()
            ),
            "technician_workload": (
                repository.get_technician_workload()
            ),
            "total_towers": (
                repository.get_total_towers()
            ),
            "tower_status": (
                repository.get_tower_status()
            ),
            "total_service_requests": (
                repository.get_total_service_requests()
            ),
            "service_request_status": (
                repository.get_service_request_status()
            ),
            "plan_utilization": (
                repository.get_plan_utilization()
            ),
        }