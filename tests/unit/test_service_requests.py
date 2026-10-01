from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.service_request import (
    ServiceRequestPriority,
    ServiceRequestStatus,
    ServiceRequestType,
)
from app.models.user import UserRole
from app.schemas.service_request import (
    ServiceRequestCompletion,
    ServiceRequestCreate,
    ServiceRequestRejection,
    ServiceRequestStatusUpdate,
    ServiceRequestUpdate,
)
from app.services.service_request_service import (
    ServiceRequestService,
)


_counter = 0


def unique_value(prefix: str) -> str:
    global _counter
    _counter += 1
    return f"{prefix}-{_counter}"


def create_user(
    db_session,
    role=UserRole.CUSTOMER,
    is_active=True,
):
    from app.models.user import User

    user = User(
        full_name=unique_value("User"),
        email=f"{unique_value('user')}@example.com",
        phone=unique_value("9"),
        hashed_password="hashed-password",
        role=role,
        is_active=is_active,
        is_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    return user


def create_customer(db_session, is_active=True):
    from app.models.customer import Customer

    user = create_user(
        db_session,
        role=UserRole.CUSTOMER,
        is_active=True,
    )

    customer = Customer(
        user_id=user.id,
        customer_number=unique_value("CUST-SR"),
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        is_active=is_active,
    )

    db_session.add(customer)
    db_session.flush()

    return customer


def create_service_request(
    db_session,
    customer=None,
    request_type=ServiceRequestType.GENERAL,
    priority=ServiceRequestPriority.MEDIUM,
):
    if customer is None:
        customer = create_customer(db_session)

    data = ServiceRequestCreate(
        request_number=unique_value("SR"),
        customer_id=customer.id,
        request_type=request_type,
        priority=priority,
        title="Test service request",
        description="Testing service request workflow",
    )

    return ServiceRequestService.create(
        db_session,
        data,
    )


def create_manager(db_session):
    return create_user(
        db_session,
        role=UserRole.OPERATIONS_MANAGER,
        is_active=True,
    )


def test_create_service_request(db_session):
    customer = create_customer(db_session)

    request = create_service_request(
        db_session,
        customer,
    )

    assert request.id is not None
    assert request.customer_id == customer.id
    assert request.status == ServiceRequestStatus.SUBMITTED


def test_duplicate_request_number_rejected(db_session):
    customer = create_customer(db_session)

    request_number = unique_value("DUP")

    data = ServiceRequestCreate(
        request_number=request_number,
        customer_id=customer.id,
        request_type=ServiceRequestType.GENERAL,
        title="First request",
        description="First request description",
    )

    ServiceRequestService.create(db_session, data)

    duplicate = ServiceRequestCreate(
        request_number=request_number,
        customer_id=customer.id,
        request_type=ServiceRequestType.GENERAL,
        title="Second request",
        description="Second request description",
    )

    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.create(
            db_session,
            duplicate,
        )

    assert exc.value.status_code == 409


def test_inactive_customer_rejected(db_session):
    customer = create_customer(
        db_session,
        is_active=False,
    )

    data = ServiceRequestCreate(
        request_number=unique_value("INACTIVE"),
        customer_id=customer.id,
        request_type=ServiceRequestType.GENERAL,
        title="Inactive customer request",
        description="Should not be accepted",
    )

    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.create(
            db_session,
            data,
        )

    assert exc.value.status_code == 400


def test_missing_customer_rejected(db_session):
    data = ServiceRequestCreate(
        request_number=unique_value("MISSING"),
        customer_id=999999,
        request_type=ServiceRequestType.GENERAL,
        title="Missing customer",
        description="Customer does not exist",
    )

    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.create(
            db_session,
            data,
        )

    assert exc.value.status_code == 404


def test_get_service_request(db_session):
    request = create_service_request(db_session)

    result = ServiceRequestService.get(
        db_session,
        request.id,
    )

    assert result.id == request.id


def test_missing_service_request_returns_404(db_session):
    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.get(
            db_session,
            999999,
        )

    assert exc.value.status_code == 404


def test_update_service_request(db_session):
    request = create_service_request(db_session)

    data = ServiceRequestUpdate(
        priority=ServiceRequestPriority.HIGH,
        title="Updated request",
        description="Updated description",
        processing_notes="Updated notes",
    )

    result = ServiceRequestService.update(
        db_session,
        request.id,
        data,
    )

    assert result.priority == ServiceRequestPriority.HIGH
    assert result.title == "Updated request"
    assert result.processing_notes == "Updated notes"


def test_submitted_to_under_review(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    result = ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    assert result.status == ServiceRequestStatus.UNDER_REVIEW
    assert result.reviewed_at is not None


def test_under_review_to_approved(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    result = ServiceRequestService.approve(
        db_session,
        request.id,
        manager,
    )

    assert result.status == ServiceRequestStatus.APPROVED
    assert result.approved_at is not None


def test_approval_requires_operations_role(db_session):
    request = create_service_request(db_session)
    customer_user = create_user(
        db_session,
        role=UserRole.CUSTOMER,
    )

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        customer_user,
    )

    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.approve(
            db_session,
            request.id,
            customer_user,
        )

    assert exc.value.status_code == 403


def test_rejection_requires_reason(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    with pytest.raises(Exception):
        ServiceRequestRejection(
            rejection_reason=" "
        )


def test_reject_service_request(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    result = ServiceRequestService.reject(
        db_session,
        request.id,
        ServiceRequestRejection(
            rejection_reason="Insufficient information",
        ),
        manager,
    )

    assert result.status == ServiceRequestStatus.REJECTED
    assert result.rejection_reason == "Insufficient information"
    assert result.rejected_at is not None


def test_approved_to_in_progress(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    ServiceRequestService.approve(
        db_session,
        request.id,
        manager,
    )

    result = ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.IN_PROGRESS,
        ),
        manager,
    )

    assert result.status == ServiceRequestStatus.IN_PROGRESS
    assert result.started_at is not None


def test_in_progress_to_completed(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    ServiceRequestService.approve(
        db_session,
        request.id,
        manager,
    )

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.IN_PROGRESS,
        ),
        manager,
    )

    result = ServiceRequestService.complete(
        db_session,
        request.id,
        ServiceRequestCompletion(
            completed_notes="Work completed successfully",
        ),
        manager,
    )

    assert result.status == ServiceRequestStatus.COMPLETED
    assert result.completed_at is not None
    assert result.completed_notes == "Work completed successfully"


def test_invalid_status_transition_rejected(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.update_status(
            db_session,
            request.id,
            ServiceRequestStatusUpdate(
                status=ServiceRequestStatus.COMPLETED,
            ),
            manager,
        )

    assert exc.value.status_code == 400


def test_same_status_rejected(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.update_status(
            db_session,
            request.id,
            ServiceRequestStatusUpdate(
                status=ServiceRequestStatus.SUBMITTED,
            ),
            manager,
        )

    assert exc.value.status_code == 400


def test_cancel_service_request(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    result = ServiceRequestService.cancel(
        db_session,
        request.id,
        manager,
    )

    assert result.status == ServiceRequestStatus.CANCELLED
    assert result.cancelled_at is not None


def test_cancelled_request_cannot_be_updated(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.cancel(
        db_session,
        request.id,
        manager,
    )

    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.update(
            db_session,
            request.id,
            ServiceRequestUpdate(
                title="Should fail",
            ),
        )

    assert exc.value.status_code == 400


def test_rejected_request_cannot_be_completed(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    ServiceRequestService.reject(
        db_session,
        request.id,
        ServiceRequestRejection(
            rejection_reason="Rejected for testing",
        ),
        manager,
    )

    with pytest.raises(HTTPException):
        ServiceRequestService.complete(
            db_session,
            request.id,
            ServiceRequestCompletion(),
            manager,
        )


def test_completed_request_cannot_be_modified(db_session):
    request = create_service_request(db_session)
    manager = create_manager(db_session)

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.UNDER_REVIEW,
        ),
        manager,
    )

    ServiceRequestService.approve(
        db_session,
        request.id,
        manager,
    )

    ServiceRequestService.update_status(
        db_session,
        request.id,
        ServiceRequestStatusUpdate(
            status=ServiceRequestStatus.IN_PROGRESS,
        ),
        manager,
    )

    ServiceRequestService.complete(
        db_session,
        request.id,
        ServiceRequestCompletion(),
        manager,
    )

    with pytest.raises(HTTPException):
        ServiceRequestService.update(
            db_session,
            request.id,
            ServiceRequestUpdate(
                title="Should fail",
            ),
        )


def test_list_service_requests(db_session):
    customer = create_customer(db_session)

    create_service_request(
        db_session,
        customer,
    )

    create_service_request(
        db_session,
        customer,
    )

    items, total = ServiceRequestService.list(
        db_session,
        page=1,
        page_size=10,
    )

    assert total >= 2
    assert len(items) >= 2


def test_list_filter_by_customer(db_session):
    customer_one = create_customer(db_session)
    customer_two = create_customer(db_session)

    create_service_request(
        db_session,
        customer_one,
    )

    create_service_request(
        db_session,
        customer_two,
    )

    items, total = ServiceRequestService.list(
        db_session,
        customer_id=customer_one.id,
    )

    assert total >= 1
    assert all(
        item.customer_id == customer_one.id
        for item in items
    )


def test_list_filter_by_type(db_session):
    customer = create_customer(db_session)

    create_service_request(
        db_session,
        customer,
        request_type=ServiceRequestType.SIM_REPLACEMENT,
    )

    items, _ = ServiceRequestService.list(
        db_session,
        request_type=ServiceRequestType.SIM_REPLACEMENT,
    )

    assert all(
        item.request_type
        == ServiceRequestType.SIM_REPLACEMENT
        for item in items
    )


def test_list_filter_by_priority(db_session):
    customer = create_customer(db_session)

    create_service_request(
        db_session,
        customer,
        priority=ServiceRequestPriority.CRITICAL,
    )

    items, _ = ServiceRequestService.list(
        db_session,
        priority=ServiceRequestPriority.CRITICAL,
    )

    assert all(
        item.priority
        == ServiceRequestPriority.CRITICAL
        for item in items
    )


def test_list_filter_by_status(db_session):
    customer = create_customer(db_session)
    manager = create_manager(db_session)

    request = create_service_request(
        db_session,
        customer,
    )

    ServiceRequestService.cancel(
        db_session,
        request.id,
        manager,
    )

    items, _ = ServiceRequestService.list(
        db_session,
        status_filter=ServiceRequestStatus.CANCELLED,
    )

    assert all(
        item.status == ServiceRequestStatus.CANCELLED
        for item in items
    )


def test_search_service_requests(db_session):
    customer = create_customer(db_session)

    data = ServiceRequestCreate(
        request_number=unique_value("SEARCH"),
        customer_id=customer.id,
        request_type=ServiceRequestType.GENERAL,
        title="Unique network replacement request",
        description="Searchable service request",
    )

    ServiceRequestService.create(
        db_session,
        data,
    )

    items, total = ServiceRequestService.list(
        db_session,
        search="Unique network replacement",
    )

    assert total >= 1
    assert any(
        "Unique network replacement" in item.title
        for item in items
    )


def test_invalid_pagination_rejected(db_session):
    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.list(
            db_session,
            page=0,
            page_size=20,
        )

    assert exc.value.status_code == 400


def test_page_size_above_limit_rejected(db_session):
    with pytest.raises(HTTPException) as exc:
        ServiceRequestService.list(
            db_session,
            page=1,
            page_size=101,
        )

    assert exc.value.status_code == 400


def test_service_request_type_values():
    assert ServiceRequestType.SIM_REPLACEMENT.value == "SIM Replacement"
    assert ServiceRequestType.DEVICE_REPLACEMENT.value == "Device Replacement"
    assert ServiceRequestType.PLAN_CHANGE.value == "Plan Change"


def test_service_request_status_values():
    assert ServiceRequestStatus.SUBMITTED.value == "Submitted"
    assert ServiceRequestStatus.COMPLETED.value == "Completed"
    assert ServiceRequestStatus.CANCELLED.value == "Cancelled"


def test_service_request_priority_values():
    assert ServiceRequestPriority.LOW.value == "Low"
    assert ServiceRequestPriority.MEDIUM.value == "Medium"
    assert ServiceRequestPriority.HIGH.value == "High"
    assert ServiceRequestPriority.CRITICAL.value == "Critical"