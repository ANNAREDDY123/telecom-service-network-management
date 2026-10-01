import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserRole
from app.api.dashboard import get_current_user
from app.db.database import get_db


client = TestClient(app)


DASHBOARD_RESPONSE = {
    "total_customers": 10,
    "active_customers": 8,
    "active_subscriptions": 7,
    "active_sims": 7,
    "total_data_usage_mb": 1250.500,
    "network_outages": 2,
    "open_tickets": 4,
    "sla_breaches": 1,
    "total_technicians": 5,
    "available_technicians": 3,
    "busy_technicians": 2,
    "technician_workload": [
        {
            "technician_id": 1,
            "technician_code": "TECH001",
            "technician_name": "Test Technician",
            "status": "Available",
            "availability": "Available",
            "active_assignments": 1,
            "completed_assignments": 3,
            "total_assignments": 4,
        }
    ],
    "total_towers": 6,
    "tower_status": [
        {
            "status": "Active",
            "count": 5,
        },
        {
            "status": "Maintenance",
            "count": 1,
        },
    ],
    "total_service_requests": 4,
    "service_request_status": [
        {
            "status": "Submitted",
            "count": 2,
        },
        {
            "status": "Completed",
            "count": 2,
        },
    ],
    "plan_utilization": [
        {
            "plan_id": 1,
            "plan_code": "PLAN001",
            "plan_name": "Premium Data Plan",
            "service_type": "Data",
            "plan_status": "Active",
            "active_subscriptions": 5,
            "data_limit_mb": 10000,
            "data_used_mb": 1250.500,
            "utilization_percentage": 2.501,
        }
    ],
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


def setup_dashboard_overrides(role: UserRole, monkeypatch):
    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_current_user] = (
        lambda: override_user(role)
    )

    monkeypatch.setattr(
        "app.api.dashboard.DashboardService.get_overview",
        lambda db: DASHBOARD_RESPONSE,
    )


@pytest.mark.parametrize(
    "role",
    [
        UserRole.SUPER_ADMIN,
        UserRole.OPERATIONS_MANAGER,
        UserRole.SUPPORT_AGENT,
        UserRole.NETWORK_ENGINEER,
        UserRole.FIELD_TECHNICIAN,
    ],
)
def test_dashboard_overview_allows_management_roles(
    role,
    monkeypatch,
):
    setup_dashboard_overrides(role, monkeypatch)

    response = client.get("/dashboard/overview")

    assert response.status_code == 200

    data = response.json()

    assert data["total_customers"] == 10
    assert data["active_customers"] == 8
    assert data["active_subscriptions"] == 7
    assert data["active_sims"] == 7
    assert data["network_outages"] == 2
    assert data["open_tickets"] == 4
    assert data["sla_breaches"] == 1


def test_dashboard_overview_returns_technician_workload(
    monkeypatch,
):
    setup_dashboard_overrides(
        UserRole.OPERATIONS_MANAGER,
        monkeypatch,
    )

    response = client.get("/dashboard/overview")

    assert response.status_code == 200

    data = response.json()

    assert len(data["technician_workload"]) == 1

    technician = data["technician_workload"][0]

    assert technician["technician_id"] == 1
    assert technician["technician_code"] == "TECH001"
    assert technician["active_assignments"] == 1
    assert technician["completed_assignments"] == 3
    assert technician["total_assignments"] == 4


def test_dashboard_overview_returns_tower_status(
    monkeypatch,
):
    setup_dashboard_overrides(
        UserRole.NETWORK_ENGINEER,
        monkeypatch,
    )

    response = client.get("/dashboard/overview")

    assert response.status_code == 200

    data = response.json()

    assert data["total_towers"] == 6
    assert len(data["tower_status"]) == 2
    assert data["tower_status"][0]["status"] == "Active"
    assert data["tower_status"][0]["count"] == 5


def test_dashboard_overview_returns_service_request_status(
    monkeypatch,
):
    setup_dashboard_overrides(
        UserRole.SUPPORT_AGENT,
        monkeypatch,
    )

    response = client.get("/dashboard/overview")

    assert response.status_code == 200

    data = response.json()

    assert data["total_service_requests"] == 4
    assert len(data["service_request_status"]) == 2


def test_dashboard_overview_returns_plan_utilization(
    monkeypatch,
):
    setup_dashboard_overrides(
        UserRole.SUPER_ADMIN,
        monkeypatch,
    )

    response = client.get("/dashboard/overview")

    assert response.status_code == 200

    data = response.json()

    assert len(data["plan_utilization"]) == 1

    plan = data["plan_utilization"][0]

    assert plan["plan_id"] == 1
    assert plan["plan_code"] == "PLAN001"
    assert plan["active_subscriptions"] == 5
    assert plan["data_limit_mb"] == 10000


def test_dashboard_overview_rejects_customer_role(
    monkeypatch,
):
    setup_dashboard_overrides(
        UserRole.CUSTOMER,
        monkeypatch,
    )

    response = client.get("/dashboard/overview")

    assert response.status_code == 403

    assert response.json()["detail"] == "Insufficient permissions"


def test_dashboard_overview_requires_authentication():
    app.dependency_overrides.clear()

    response = client.get("/dashboard/overview")

    assert response.status_code == 401