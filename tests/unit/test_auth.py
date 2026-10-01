from fastapi.testclient import TestClient

from app.db.database import Base, engine
from app.main import app


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_customer():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Customer",
            "email": "test.customer@example.com",
            "phone": "9876543210",
            "password": "Test@12345",
            "role": "Customer",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test.customer@example.com"
    assert data["role"] == "Customer"
    assert data["is_active"] is True


def test_login_customer():
    response = client.post(
        "/auth/login",
        json={
            "email": "test.customer@example.com",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"