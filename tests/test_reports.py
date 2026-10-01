import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserRole
from app.api.reports import get_current_user
from app.db.database import get_db


client = TestClient(app)


REPORT_OVERVIEW = {
    "report_generated_at": "2026-10-01T10:00:00",
    "customers": {
        "total_customers": 10,
        "active_customers": 8,
        "inactive_customers": 2,
        "verified_kyc_customers": 7,
        "pending_kyc_customers": 2,
        "rejected_kyc_customers": 1,
        "active_subscriptions": 7,
        "active_sims": 7,
    },
    "total_data_usage_mb": 1250.500,
    "active_subscriptions": 7,
    "active_sims": 7,
    "total_towers": 6,
    "active_outages": 1,
    "total_tickets": 10,
    "open_tickets": 4,
    "sla_breaches": 2,
    "total_service_requests": 5,
    "completed_service_requests": 3,
    "total_technicians": 5,
    "available_technicians": 3,
    "busy_technicians": 2,
}


CUSTOMER_REPORT = {
    "total_customers": 10,
    "active_customers": 8,
    "inactive_customers": 2,
    "verified_kyc_customers": 7,
    "pending_kyc_customers": 2,
    "rejected_kyc_customers": 1,
    "active_subscriptions": 7,
    "active_sims": 7,
}


USAGE_REPORT = {
    "items": [],
    "total_data_used_mb": 0,
    "total_records": 0,
    "page": 1,
    "page_size": 20,
    "total_pages": 0,
}


NETWORK_REPORT = {
    "total_towers": 6,
    "active_towers": 5,
    "maintenance_towers": 1,
    "inactive_towers": 0,
    "total_outages": 2,
    "active_outages": 1,
    "restored_outages": 1,
    "total_outage_duration_minutes": 120,
    "outages": [],
    "page": 1,
    "page_size": 20,
    "total_pages": 0,
}


SUPPORT_REPORT = {
    "total_tickets": 10,
    "open_tickets": 4,
    "in_progress_tickets": 2,
    "resolved_tickets": 2,
    "closed_tickets": 1,
    "cancelled_tickets": 1,
    "high_priority_tickets": 3,
    "sla_breaches": 2,
    "response_breaches": 1,
    "resolution_breaches": 1,
    "average_resolution_minutes": 90,
    "average_response_minutes": 15,
    "tickets": [],
    "page": 1,
    "page_size": 20,
    "total_pages": 0,
}


TECHNICIAN_REPORT = {
    "total_technicians": 5,
    "available_technicians": 3,
    "busy_technicians": 2,
    "total_assignments": 10,
    "completed_assignments": 7,
    "overall_completion_rate": 70,
    "technicians": [],
}


@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()


def override_database():
    yield None


def override_user(role: UserRole):
    return User(
        id=1,
        full_name="Test User",
        email="test@example.com",
        phone="9999999999",
        hashed_password="test-password",
        role=role,
        is_active=True,
        is_verified=True,
    )


def setup_overrides(role: UserRole, monkeypatch):
    app.dependency_overrides[get_db] = override_database

    app.dependency_overrides[get_current_user] = (
        lambda: override_user(role)
    )


def test_reports_overview_allows_super_admin(
    monkeypatch,
):
    setup_overrides(
        UserRole.SUPER_ADMIN,
        monkeypatch,
    )

    monkeypatch.setattr(
        "app.api.reports.ReportsService.get_overview",
        lambda db: REPORT_OVERVIEW,
    )

    response = client.get(
        "/reports/overview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customers"]["total_customers"] == 10
    assert data["total_towers"] == 6
    assert data["total_tickets"] == 10
    assert data["sla_breaches"] == 2


def test_customer_summary_report(
    monkeypatch,
):
    setup_overrides(
        UserRole.OPERATIONS_MANAGER,
        monkeypatch,
    )

    monkeypatch.setattr(
        "app.api.reports.ReportsService.get_customer_summary",
        lambda **kwargs: CUSTOMER_REPORT,
    )

    response = client.get(
        "/reports/customer-summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_customers"] == 10
    assert data["active_customers"] == 8
    assert data["verified_kyc_customers"] == 7


def test_usage_report(
    monkeypatch,
):
    setup_overrides(
        UserRole.SUPPORT_AGENT,
        monkeypatch,
    )

    monkeypatch.setattr(
        "app.api.reports.ReportsService.get_usage_report",
        lambda **kwargs: USAGE_REPORT,
    )

    response = client.get(
        "/reports/usage?page=1&page_size=20"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_records"] == 0


def test_network_report(
    monkeypatch,
):
    setup_overrides(
        UserRole.NETWORK_ENGINEER,
        monkeypatch,
    )

    monkeypatch.setattr(
        "app.api.reports.ReportsService.get_network_report",
        lambda **kwargs: NETWORK_REPORT,
    )

    response = client.get(
        "/reports/network"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_towers"] == 6
    assert data["active_outages"] == 1


def test_support_report(
    monkeypatch,
):
    setup_overrides(
        UserRole.SUPPORT_AGENT,
        monkeypatch,
    )

    monkeypatch.setattr(
        "app.api.reports.ReportsService.get_support_report",
        lambda **kwargs: SUPPORT_REPORT,
    )

    response = client.get(
        "/reports/support"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_tickets"] == 10
    assert data["open_tickets"] == 4
    assert data["sla_breaches"] == 2


def test_technician_report(
    monkeypatch,
):
    setup_overrides(
        UserRole.NETWORK_ENGINEER,
        monkeypatch,
    )

    monkeypatch.setattr(
        "app.api.reports.ReportsService.get_technician_report",
        lambda **kwargs: TECHNICIAN_REPORT,
    )

    response = client.get(
        "/reports/technicians"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_technicians"] == 5
    assert data["available_technicians"] == 3
    assert data["overall_completion_rate"] == 70


def test_customer_role_cannot_access_reports(
    monkeypatch,
):
    setup_overrides(
        UserRole.CUSTOMER,
        monkeypatch,
    )

    response = client.get(
        "/reports/overview"
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Insufficient permissions"
    )


def test_invalid_report_date_range(
    monkeypatch,
):
    setup_overrides(
        UserRole.SUPER_ADMIN,
        monkeypatch,
    )

    response = client.get(
        "/reports/customer-summary"
        "?start_date=2026-10-10"
        "&end_date=2026-10-01"
    )

    assert response.status_code == 422


def test_report_requires_authentication():
    app.dependency_overrides.clear()

    response = client.get(
        "/reports/overview"
    )

    assert response.status_code == 401