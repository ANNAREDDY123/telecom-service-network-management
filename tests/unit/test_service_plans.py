from fastapi.testclient import TestClient

from app.db.database import Base, engine
from app.main import app


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_create_service_plan_requires_authentication():
    response = client.post(
        "/service-plans",
        json={
            "plan_code": "DATA100",
            "plan_name": "Data 100",
            "description": "100 GB data plan",
            "plan_type": "Prepaid",
            "service_type": "Data",
            "price": 499,
            "validity_days": 28,
            "data_limit_mb": 102400,
            "voice_limit_minutes": 0,
            "sms_limit": 100,
        },
    )

    assert response.status_code in (401, 403)


def test_service_plan_route_exists():
    response = client.get(
        "/service-plans"
    )

    assert response.status_code in (401, 403)