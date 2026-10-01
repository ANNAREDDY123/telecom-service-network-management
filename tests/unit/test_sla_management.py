from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.customer import Customer
from app.models.sla_policy import SLAPolicy, SLAPriority, SLAStatus
from app.models.sla_tracking import SLATracking, SLATrackingStatus
from app.models.support_ticket import (
    SupportTicket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    TicketSource,
)
from app.models.user import User, UserRole
from app.schemas.sla import SLAPolicyCreate, SLAPolicyUpdate
from app.services.sla_service import SLAService


# ============================================================
# TEST HELPERS
# ============================================================


_counter = 0


def unique_value(prefix: str) -> str:
    global _counter
    _counter += 1
    return f"{prefix}-{_counter}"


def create_user(
    db_session,
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
):
    user = User(
        full_name=unique_value("Test User"),
        email=f"{unique_value('user').lower()}@example.com",
        phone=f"9{_counter + 1000000000}",
        hashed_password="hashed-password",
        role=role,
        is_active=is_active,
        is_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    return user


def create_customer(db_session):
    user = create_user(
        db_session,
        role=UserRole.CUSTOMER,
        is_active=True,
    )

    customer = Customer(
        user_id=user.id,
        customer_number=unique_value("CUST-SLA"),
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        is_active=True,
    )

    db_session.add(customer)
    db_session.flush()

    return customer


def create_ticket(
    db_session,
    priority: TicketPriority = TicketPriority.HIGH,
):
    customer = create_customer(db_session)

    ticket = SupportTicket(
        customer_id=customer.id,
        ticket_number=unique_value("TKT"),
        title="Network connectivity issue",
        description="Customer is unable to access the telecom service.",
        category=TicketCategory.NETWORK,
        priority=priority,
        status=TicketStatus.OPEN,
        source=TicketSource.PORTAL,
    )

    db_session.add(ticket)
    db_session.flush()

    return ticket


def create_policy(
    db_session,
    code: str | None = None,
    priority: SLAPriority = SLAPriority.HIGH,
    response_minutes: int = 30,
    resolution_minutes: int = 120,
    active: bool = True,
):
    policy = SLAPolicy(
        sla_code=code or unique_value("SLA"),
        sla_name="Standard SLA",
        priority=priority,
        response_time_minutes=response_minutes,
        resolution_time_minutes=resolution_minutes,
        status=(
            SLAStatus.ACTIVE
            if active
            else SLAStatus.INACTIVE
        ),
        description="Test SLA policy",
        is_active=active,
    )

    db_session.add(policy)
    db_session.flush()

    return policy


def create_tracking(
    db_session,
    ticket,
    policy,
    start_time=None,
):
    service = SLAService()

    return service.create_tracking_for_ticket(
        db_session,
        ticket,
        policy,
        start_time=start_time,
    )


# ============================================================
# POLICY CREATION
# ============================================================


def test_create_sla_policy(db_session):
    service = SLAService()

    data = SLAPolicyCreate(
        sla_code="SLA-HIGH-001",
        sla_name="High Priority SLA",
        priority=SLAPriority.HIGH,
        response_time_minutes=30,
        resolution_time_minutes=120,
        description="High priority support SLA",
    )

    policy = service.create_policy(
        db_session,
        data,
    )

    assert policy.id is not None
    assert policy.sla_code == "SLA-HIGH-001"
    assert policy.priority == SLAPriority.HIGH
    assert policy.response_time_minutes == 30
    assert policy.resolution_time_minutes == 120
    assert policy.status == SLAStatus.ACTIVE
    assert policy.is_active is True


def test_duplicate_sla_code_rejected(db_session):
    service = SLAService()

    data = SLAPolicyCreate(
        sla_code="SLA-DUPLICATE",
        sla_name="First SLA",
        priority=SLAPriority.MEDIUM,
        response_time_minutes=30,
        resolution_time_minutes=90,
    )

    service.create_policy(
        db_session,
        data,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_policy(
            db_session,
            data,
        )

    assert exc.value.status_code == 409


def test_resolution_time_must_be_greater_than_response_time(
    db_session,
):
    service = SLAService()

    data = SLAPolicyCreate(
        sla_code="SLA-INVALID-TIME",
        sla_name="Invalid SLA",
        priority=SLAPriority.HIGH,
        response_time_minutes=120,
        resolution_time_minutes=60,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_policy(
            db_session,
            data,
        )

    assert exc.value.status_code == 400


# ============================================================
# POLICY RETRIEVAL / UPDATE
# ============================================================


def test_get_sla_policy(db_session):
    service = SLAService()

    policy = create_policy(db_session)

    result = service.get_policy(
        db_session,
        policy.id,
    )

    assert result.id == policy.id
    assert result.sla_code == policy.sla_code


def test_missing_sla_policy_returns_404(db_session):
    service = SLAService()

    with pytest.raises(HTTPException) as exc:
        service.get_policy(
            db_session,
            999999,
        )

    assert exc.value.status_code == 404


def test_update_sla_policy(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    data = SLAPolicyUpdate(
        sla_name="Updated SLA",
        response_time_minutes=45,
        resolution_time_minutes=180,
        description="Updated description",
    )

    result = service.update_policy(
        db_session,
        policy.id,
        data,
    )

    assert result.sla_name == "Updated SLA"
    assert result.response_time_minutes == 45
    assert result.resolution_time_minutes == 180
    assert result.description == "Updated description"


def test_invalid_updated_time_configuration_rejected(
    db_session,
):
    service = SLAService()

    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    data = SLAPolicyUpdate(
        response_time_minutes=150,
        resolution_time_minutes=100,
    )

    with pytest.raises(HTTPException) as exc:
        service.update_policy(
            db_session,
            policy.id,
            data,
        )

    assert exc.value.status_code == 400


def test_inactive_policy_cannot_be_updated(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        active=False,
    )

    data = SLAPolicyUpdate(
        sla_name="Should Fail",
    )

    with pytest.raises(HTTPException) as exc:
        service.update_policy(
            db_session,
            policy.id,
            data,
        )

    assert exc.value.status_code == 400


# ============================================================
# POLICY STATUS
# ============================================================


def test_deactivate_sla_policy(db_session):
    service = SLAService()

    policy = create_policy(db_session)

    result = service.update_policy_status(
        db_session,
        policy.id,
        SLAStatus.INACTIVE,
    )

    assert result.status == SLAStatus.INACTIVE
    assert result.is_active is False


def test_reactivate_sla_policy(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        active=False,
    )

    result = service.update_policy_status(
        db_session,
        policy.id,
        SLAStatus.ACTIVE,
    )

    assert result.status == SLAStatus.ACTIVE
    assert result.is_active is True


def test_same_policy_status_rejected(db_session):
    service = SLAService()

    policy = create_policy(db_session)

    with pytest.raises(HTTPException) as exc:
        service.update_policy_status(
            db_session,
            policy.id,
            SLAStatus.ACTIVE,
        )

    assert exc.value.status_code == 400


# ============================================================
# POLICY LIST / PAGINATION
# ============================================================


def test_list_sla_policies(db_session):
    service = SLAService()

    create_policy(
        db_session,
        priority=SLAPriority.LOW,
    )
    create_policy(
        db_session,
        priority=SLAPriority.MEDIUM,
    )
    create_policy(
        db_session,
        priority=SLAPriority.HIGH,
    )

    items, total = service.list_policies(
        db_session,
        page=1,
        page_size=2,
    )

    assert len(items) == 2
    assert total == 3


def test_list_sla_policies_filter_by_priority(db_session):
    service = SLAService()

    create_policy(
        db_session,
        priority=SLAPriority.LOW,
    )
    create_policy(
        db_session,
        priority=SLAPriority.HIGH,
    )

    items, total = service.list_policies(
        db_session,
        page=1,
        page_size=10,
        priority=SLAPriority.HIGH,
    )

    assert total == 1
    assert items[0].priority == SLAPriority.HIGH


def test_list_sla_policies_filter_by_status(db_session):
    service = SLAService()

    create_policy(
        db_session,
        active=True,
    )
    create_policy(
        db_session,
        active=False,
    )

    items, total = service.list_policies(
        db_session,
        page=1,
        page_size=10,
        status=SLAStatus.INACTIVE,
    )

    assert total == 1
    assert items[0].status == SLAStatus.INACTIVE


def test_list_sla_policies_search(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        code="SLA-SEARCH-001",
    )

    items, total = service.list_policies(
        db_session,
        page=1,
        page_size=10,
        search="SEARCH-001",
    )

    assert total == 1
    assert items[0].id == policy.id


def test_invalid_policy_pagination_rejected(db_session):
    service = SLAService()

    with pytest.raises(HTTPException) as exc:
        service.list_policies(
            db_session,
            page=0,
            page_size=10,
        )

    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        service.list_policies(
            db_session,
            page=1,
            page_size=101,
        )

    assert exc.value.status_code == 400


# ============================================================
# DEADLINE CALCULATION
# ============================================================


def test_calculate_sla_deadlines(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    response_deadline, resolution_deadline = (
        service.calculate_deadlines(
            policy,
            start,
        )
    )

    assert response_deadline == start + timedelta(minutes=30)
    assert resolution_deadline == start + timedelta(minutes=120)


def test_calculate_deadlines_with_naive_datetime(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        response_minutes=15,
        resolution_minutes=60,
    )

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
    )

    response_deadline, resolution_deadline = (
        service.calculate_deadlines(
            policy,
            start,
        )
    )

    assert response_deadline.tzinfo == timezone.utc
    assert resolution_deadline.tzinfo == timezone.utc


def test_inactive_policy_cannot_calculate_deadlines(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        active=False,
    )

    with pytest.raises(HTTPException) as exc:
        service.calculate_deadlines(
            policy,
            datetime.now(timezone.utc),
        )

    assert exc.value.status_code == 400


# ============================================================
# ACTIVE POLICY SELECTION
# ============================================================


def test_active_policy_selected_for_priority(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        priority=SLAPriority.HIGH,
        active=True,
    )

    result = service.get_active_policy_for_priority(
        db_session,
        SLAPriority.HIGH,
    )

    assert result.id == policy.id


def test_inactive_policy_not_selected(db_session):
    service = SLAService()

    create_policy(
        db_session,
        priority=SLAPriority.CRITICAL,
        active=False,
    )

    with pytest.raises(HTTPException) as exc:
        service.get_active_policy_for_priority(
            db_session,
            SLAPriority.CRITICAL,
        )

    assert exc.value.status_code == 404


# ============================================================
# SLA TRACKING CREATION
# ============================================================


def test_create_tracking_for_ticket(db_session):
    service = SLAService()

    ticket = create_ticket(
        db_session,
        priority=TicketPriority.HIGH,
    )

    policy = create_policy(
        db_session,
        priority=SLAPriority.HIGH,
        response_minutes=30,
        resolution_minutes=120,
    )

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    tracking = service.create_tracking_for_ticket(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    assert tracking.id is not None
    assert tracking.ticket_id == ticket.id
    assert tracking.sla_policy_id == policy.id

    assert tracking.response_deadline == (
        start + timedelta(minutes=30)
    )

    assert tracking.resolution_deadline == (
        start + timedelta(minutes=120)
    )

    assert tracking.status == SLATrackingStatus.ON_TRACK


def test_duplicate_tracking_rejected(db_session):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    service.create_tracking_for_ticket(
        db_session,
        ticket,
        policy,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_tracking_for_ticket(
            db_session,
            ticket,
            policy,
        )

    assert exc.value.status_code == 409


def test_closed_ticket_cannot_get_sla_tracking(db_session):
    service = SLAService()

    ticket = create_ticket(db_session)
    ticket.status = TicketStatus.CLOSED
    db_session.flush()

    policy = create_policy(db_session)

    with pytest.raises(HTTPException) as exc:
        service.create_tracking_for_ticket(
            db_session,
            ticket,
            policy,
        )

    assert exc.value.status_code == 400


def test_cancelled_ticket_cannot_get_sla_tracking(db_session):
    service = SLAService()

    ticket = create_ticket(db_session)
    ticket.status = TicketStatus.CANCELLED
    db_session.flush()

    policy = create_policy(db_session)

    with pytest.raises(HTTPException) as exc:
        service.create_tracking_for_ticket(
            db_session,
            ticket,
            policy,
        )

    assert exc.value.status_code == 400


def test_tracking_automatically_selects_priority_policy(
    db_session,
):
    service = SLAService()

    ticket = create_ticket(
        db_session,
        priority=TicketPriority.HIGH,
    )

    policy = create_policy(
        db_session,
        priority=SLAPriority.HIGH,
    )

    tracking = service.create_tracking_for_ticket(
        db_session,
        ticket,
    )

    assert tracking.sla_policy_id == policy.id


# ============================================================
# TRACKING RETRIEVAL
# ============================================================


def test_get_tracking(db_session):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
    )

    result = service.get_tracking(
        db_session,
        tracking.id,
    )

    assert result.id == tracking.id
    assert result.ticket_id == ticket.id


def test_missing_tracking_returns_404(db_session):
    service = SLAService()

    with pytest.raises(HTTPException) as exc:
        service.get_tracking(
            db_session,
            999999,
        )

    assert exc.value.status_code == 404


def test_get_tracking_by_ticket(db_session):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
    )

    result = service.get_tracking_by_ticket(
        db_session,
        ticket.id,
    )

    assert result.id == tracking.id


# ============================================================
# RESPONSE TRACKING
# ============================================================


def test_record_response_within_sla(db_session):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    response_time = start + timedelta(minutes=20)

    result = service.record_response(
        db_session,
        tracking.id,
        response_time,
    )

    assert result.response_at == response_time
    assert result.response_breached is False


def test_record_response_after_deadline_marks_breach(
    db_session,
):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    response_time = start + timedelta(minutes=45)

    result = service.record_response(
        db_session,
        tracking.id,
        response_time,
    )

    assert result.response_at == response_time
    assert result.response_breached is True
    assert result.status == SLATrackingStatus.RESPONSE_BREACHED


def test_duplicate_response_rejected(db_session):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
    )

    first_response = datetime.now(timezone.utc)

    service.record_response(
        db_session,
        tracking.id,
        first_response,
    )

    with pytest.raises(HTTPException) as exc:
        service.record_response(
            db_session,
            tracking.id,
            first_response + timedelta(minutes=1),
        )

    assert exc.value.status_code == 400


# ============================================================
# RESOLUTION TRACKING
# ============================================================


def test_record_resolution_within_sla(db_session):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    resolved_time = start + timedelta(minutes=90)

    result = service.record_resolution(
        db_session,
        tracking.id,
        resolved_time,
    )

    assert result.resolved_at == resolved_time
    assert result.resolution_breached is False
    assert result.status == SLATrackingStatus.COMPLETED


def test_record_resolution_after_deadline_marks_breach(
    db_session,
):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    resolved_time = start + timedelta(minutes=180)

    result = service.record_resolution(
        db_session,
        tracking.id,
        resolved_time,
    )

    assert result.resolution_breached is True
    assert result.status == SLATrackingStatus.RESOLUTION_BREACHED


def test_duplicate_resolution_rejected(db_session):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
    )

    resolved_time = datetime.now(timezone.utc)

    service.record_resolution(
        db_session,
        tracking.id,
        resolved_time,
    )

    with pytest.raises(HTTPException) as exc:
        service.record_resolution(
            db_session,
            tracking.id,
            resolved_time + timedelta(minutes=1),
        )

    assert exc.value.status_code == 400


def test_resolution_before_tracking_creation_rejected(
    db_session,
):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
    )

    created_at = (
        tracking.created_at
        if tracking.created_at.tzinfo
        else tracking.created_at.replace(tzinfo=timezone.utc)
    )

    invalid_resolution = created_at - timedelta(minutes=1)

    with pytest.raises(HTTPException) as exc:
        service.record_resolution(
            db_session,
            tracking.id,
            invalid_resolution,
        )

    assert exc.value.status_code == 400


# ============================================================
# BREACH DETECTION
# ============================================================


def test_response_breach_detected(db_session):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    check_time = start + timedelta(minutes=45)

    result = service.detect_breaches(
        db_session,
        tracking.id,
        check_time,
    )

    assert result.response_breached is True
    assert result.resolution_breached is False
    assert result.status == SLATrackingStatus.RESPONSE_BREACHED


def test_resolution_breach_detected(db_session):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    check_time = start + timedelta(minutes=180)

    result = service.detect_breaches(
        db_session,
        tracking.id,
        check_time,
    )

    assert result.response_breached is True
    assert result.resolution_breached is True
    assert result.status == SLATrackingStatus.BOTH_BREACHED


def test_no_breach_before_deadlines(db_session):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    check_time = start + timedelta(minutes=10)

    result = service.detect_breaches(
        db_session,
        tracking.id,
        check_time,
    )

    assert result.response_breached is False
    assert result.resolution_breached is False
    assert result.status == SLATrackingStatus.ON_TRACK


def test_completed_tracking_status(db_session):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    response_time = start + timedelta(minutes=10)
    resolution_time = start + timedelta(minutes=90)

    service.record_response(
        db_session,
        tracking.id,
        response_time,
    )

    result = service.record_resolution(
        db_session,
        tracking.id,
        resolution_time,
    )

    assert result.status == SLATrackingStatus.COMPLETED
    assert result.response_breached is False
    assert result.resolution_breached is False


# ============================================================
# BOTH BREACHES
# ============================================================


def test_both_sla_breaches_detected(db_session):
    service = SLAService()

    start = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ticket = create_ticket(db_session)
    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
        start_time=start,
    )

    late_response = start + timedelta(minutes=60)
    late_resolution = start + timedelta(minutes=180)

    service.record_response(
        db_session,
        tracking.id,
        late_response,
    )

    result = service.record_resolution(
        db_session,
        tracking.id,
        late_resolution,
    )

    assert result.response_breached is True
    assert result.resolution_breached is True
    assert result.status == SLATrackingStatus.BOTH_BREACHED


# ============================================================
# TRACKING PAGINATION / FILTERING
# ============================================================


def test_list_sla_tracking_pagination(db_session):
    service = SLAService()

    policy = create_policy(db_session)

    for _ in range(3):
        ticket = create_ticket(db_session)

        create_tracking(
            db_session,
            ticket,
            policy,
        )

    items, total = service.list_tracking(
        db_session,
        page=1,
        page_size=2,
    )

    assert len(items) == 2
    assert total == 3


def test_list_sla_tracking_filter_by_policy(db_session):
    service = SLAService()

    policy_one = create_policy(
        db_session,
        priority=SLAPriority.HIGH,
    )

    policy_two = create_policy(
        db_session,
        priority=SLAPriority.CRITICAL,
    )

    ticket_one = create_ticket(db_session)
    ticket_two = create_ticket(db_session)

    create_tracking(
        db_session,
        ticket_one,
        policy_one,
    )

    create_tracking(
        db_session,
        ticket_two,
        policy_two,
    )

    items, total = service.list_tracking(
        db_session,
        page=1,
        page_size=10,
        policy_id=policy_one.id,
    )

    assert total == 1
    assert items[0].sla_policy_id == policy_one.id


def test_list_sla_tracking_filter_by_ticket(db_session):
    service = SLAService()

    policy = create_policy(db_session)

    ticket_one = create_ticket(db_session)
    ticket_two = create_ticket(db_session)

    tracking_one = create_tracking(
        db_session,
        ticket_one,
        policy,
    )

    create_tracking(
        db_session,
        ticket_two,
        policy,
    )

    items, total = service.list_tracking(
        db_session,
        page=1,
        page_size=10,
        ticket_id=ticket_one.id,
    )

    assert total == 1
    assert items[0].id == tracking_one.id


def test_list_sla_tracking_filter_by_status(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    ticket_one = create_ticket(db_session)
    ticket_two = create_ticket(db_session)

    tracking_one = create_tracking(
        db_session,
        ticket_one,
        policy,
    )

    tracking_two = create_tracking(
        db_session,
        ticket_two,
        policy,
    )

    future_time = (
        datetime.now(timezone.utc)
        + timedelta(hours=3)
    )

    service.detect_breaches(
        db_session,
        tracking_two.id,
        future_time,
    )

    items, total = service.list_tracking(
        db_session,
        page=1,
        page_size=10,
        status=SLATrackingStatus.ON_TRACK,
    )

    assert total >= 1
    assert all(
        item.status == SLATrackingStatus.ON_TRACK
        for item in items
    )


def test_invalid_tracking_pagination_rejected(db_session):
    service = SLAService()

    with pytest.raises(HTTPException) as exc:
        service.list_tracking(
            db_session,
            page=0,
            page_size=10,
        )

    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        service.list_tracking(
            db_session,
            page=1,
            page_size=101,
        )

    assert exc.value.status_code == 400


# ============================================================
# BULK BREACH CHECK
# ============================================================


def test_check_all_active_breaches(db_session):
    service = SLAService()

    policy = create_policy(
        db_session,
        response_minutes=30,
        resolution_minutes=120,
    )

    ticket_one = create_ticket(db_session)
    ticket_two = create_ticket(db_session)

    create_tracking(
        db_session,
        ticket_one,
        policy,
    )

    create_tracking(
        db_session,
        ticket_two,
        policy,
    )

    future_time = (
        datetime.now(timezone.utc)
        + timedelta(hours=3)
    )

    count = service.check_all_active_breaches(
        db_session,
        future_time,
    )

    assert count == 2


# ============================================================
# SERVICE DEFAULT RESPONSE / RESOLUTION
# ============================================================


def test_record_response_uses_current_time_when_not_supplied(
    db_session,
):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
    )

    before = datetime.now(timezone.utc)

    result = service.record_response(
        db_session,
        tracking.id,
    )

    after = datetime.now(timezone.utc)

    response_at = result.response_at

    assert response_at is not None
    assert before <= response_at <= after


def test_record_resolution_uses_current_time_when_not_supplied(
    db_session,
):
    service = SLAService()

    ticket = create_ticket(db_session)
    policy = create_policy(db_session)

    tracking = create_tracking(
        db_session,
        ticket,
        policy,
    )

    before = datetime.now(timezone.utc)

    result = service.record_resolution(
        db_session,
        tracking.id,
    )

    after = datetime.now(timezone.utc)

    resolved_at = result.resolved_at

    assert resolved_at is not None
    assert before <= resolved_at <= after