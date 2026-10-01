from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService
from app.middleware.audit_middleware import (
    extract_user_id_from_token,
    get_action,
    get_resource_id,
    get_resource_name,
)


client = TestClient(app)


def create_admin():
    return User(
        id=1,
        full_name="Audit Admin",
        email="audit-admin@example.com",
        hashed_password="hashed",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_verified=True,
    )


def create_customer():
    return User(
        id=2,
        full_name="Audit Customer",
        email="audit-customer@example.com",
        hashed_password="hashed",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
    )


def test_audit_model_can_be_created(
    db_session,
):

    user = create_admin()

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    audit = AuditLog(
        user_id=user.id,
        action="CREATE",
        resource="customers",
        resource_id=10,
        method="POST",
        endpoint="/customers/",
        status_code=201,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="test-request-001",
        details="Test audit event",
    )

    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    assert audit.id is not None
    assert audit.user_id == user.id
    assert audit.action == "CREATE"
    assert audit.resource == "customers"
    assert audit.resource_id == 10
    assert audit.method == "POST"
    assert audit.status_code == 201


def test_audit_service_create(
    db_session,
):

    user = create_admin()

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    data = AuditLogCreate(
        user_id=user.id,
        action="UPDATE",
        resource="service-plans",
        resource_id=5,
        method="PATCH",
        endpoint="/service-plans/5",
        status_code=200,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="service-test-001",
        details="Plan updated",
    )

    result = AuditLogService.create(
        db_session,
        data,
    )

    assert result.id is not None
    assert result.user_id == user.id
    assert result.action == "UPDATE"
    assert result.resource == "service-plans"


def test_audit_service_list(
    db_session,
):

    user = create_admin()

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    for index in range(3):
        audit = AuditLog(
            user_id=user.id,
            action="CREATE",
            resource="customers",
            resource_id=index + 1,
            method="POST",
            endpoint="/customers/",
            status_code=201,
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_id=f"list-test-{index}",
            details=None,
        )

        db_session.add(audit)

    db_session.commit()

    result = AuditLogService.list_logs(
        db_session,
        user_id=user.id,
        page=1,
        page_size=2,
    )

    assert result["total"] == 3
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert result["total_pages"] == 2
    assert len(result["items"]) == 2


def test_audit_service_filters_by_action(
    db_session,
):

    user = create_admin()

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    db_session.add(
        AuditLog(
            user_id=user.id,
            action="CREATE",
            resource="customers",
            method="POST",
            endpoint="/customers/",
            status_code=201,
        )
    )

    db_session.add(
        AuditLog(
            user_id=user.id,
            action="DELETE",
            resource="customers",
            resource_id=5,
            method="DELETE",
            endpoint="/customers/5",
            status_code=204,
        )
    )

    db_session.commit()

    result = AuditLogService.list_logs(
        db_session,
        action="DELETE",
    )

    assert result["total"] == 1
    assert result["items"][0].action == "DELETE"


def test_audit_service_filters_by_date(
    db_session,
):

    user = create_admin()

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    audit = AuditLog(
        user_id=user.id,
        action="CREATE",
        resource="devices",
        method="POST",
        endpoint="/devices/",
        status_code=201,
        created_at=datetime.now(timezone.utc),
    )

    db_session.add(audit)
    db_session.commit()

    today = date.today()

    result = AuditLogService.list_logs(
        db_session,
        start_date=today,
        end_date=today,
    )

    assert result["total"] >= 1


def test_invalid_date_range(
    db_session,
):

    with pytest.raises(Exception):
        AuditLogService.list_logs(
            db_session,
            start_date=date(
                2026,
                10,
                10,
            ),
            end_date=date(
                2026,
                10,
                1,
            ),
        )


def test_audit_middleware_helpers():

    assert get_action("POST") == "CREATE"
    assert get_action("PUT") == "UPDATE"
    assert get_action("PATCH") == "UPDATE"
    assert get_action("DELETE") == "DELETE"

    assert (
        get_resource_name(
            "/customers/25"
        )
        == "customers"
    )

    assert (
        get_resource_id(
            "/customers/25"
        )
        == 25
    )

    assert (
        get_resource_id(
            "/customers"
        )
        is None
    )


def test_invalid_authorization_returns_no_user():

    assert (
        extract_user_id_from_token(
            None
        )
        is None
    )

    assert (
        extract_user_id_from_token(
            "Invalid token"
        )
        is None
    )

    assert (
        extract_user_id_from_token(
            "Bearer invalid-token"
        )
        is None
    )