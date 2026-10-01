from datetime import datetime

import pytest
from fastapi import HTTPException

from app.models.customer import Customer
from app.models.network_outage import NetworkOutage
from app.models.support_ticket import (
    SupportTicket,
    TicketCategory,
    TicketPriority,
    TicketSource,
    TicketStatus,
)
from app.models.user import User, UserRole
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketUpdate,
    TicketResolution,
    TicketStatusUpdate,
)
from app.services.support_ticket_service import SupportTicketService
from app.core.security import hash_password


_user_counter = 0


def create_user(
    db,
    email="customer@example.com",
    role=UserRole.CUSTOMER,
):
    global _user_counter
    _user_counter += 1

    phone = f"900000{_user_counter:04d}"

    user = User(
        full_name="Test User",
        email=email,
        phone=phone,
        hashed_password=hash_password("Test@12345"),
        role=role,
        is_active=True,
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_customer(
    db,
    email="customer@example.com",
    is_active=True,
):
    user = create_user(
        db,
        email=email,
        role=UserRole.CUSTOMER,
    )

    customer = Customer(
        user_id=user.id,
        customer_number=f"CUST-{user.id:05d}",
        full_name="Test Customer",
        email=email,
        phone=user.phone,
        is_active=is_active,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_outage(db):
    from app.models.network_tower import NetworkTower

    tower = NetworkTower(
        tower_code="TWR-TEST-001",
        tower_name="Test Tower",
        tower_type="Macro",
        status="Active",
        latitude=17.3850,
        longitude=78.4867,
        address="Test Tower Address",
        city="Hyderabad",
        state="Telangana",
        postal_code="500001",
        coverage_radius_km=5.0,
        capacity=1000,
        installation_date=datetime.utcnow(),
    )

    db.add(tower)
    db.commit()
    db.refresh(tower)

    outage = NetworkOutage(
    outage_number="OUT-TEST-001",
    title="Test Network Outage",
    description="Network outage for support ticket test",
    outage_type="Network",
    severity="HIGH",
    status="REPORTED",
    tower_id=tower.id,
    start_time=datetime.utcnow(),
)

    db.add(outage)
    db.commit()
    db.refresh(outage)

    return outage


def create_ticket(
    db,
    customer_id,
    ticket_number="TKT-001",
    outage_id=None,
):
    service = SupportTicketService()

    data = SupportTicketCreate(
        customer_id=customer_id,
        outage_id=outage_id,
        ticket_number=ticket_number,
        title="No network connectivity",
        description="Customer is unable to connect to the network",
        category=TicketCategory.NETWORK,
        priority=TicketPriority.HIGH,
        source=TicketSource.PORTAL,
    )

    return service.create_ticket(db, data)


def test_create_ticket(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    assert ticket.id is not None
    assert ticket.ticket_number == "TKT-001"
    assert ticket.customer_id == customer.id
    assert ticket.status == TicketStatus.OPEN
    assert ticket.priority == TicketPriority.HIGH


def test_inactive_customer_cannot_create_ticket(db_session):
    customer = create_customer(
        db_session,
        email="inactive@example.com",
        is_active=False,
    )

    service = SupportTicketService()

    data = SupportTicketCreate(
        customer_id=customer.id,
        ticket_number="TKT-INACTIVE",
        title="Test ticket",
        description="Testing inactive customer",
        category=TicketCategory.NETWORK,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_ticket(
            db_session,
            data,
        )

    assert exc.value.status_code == 400


def test_duplicate_ticket_number_rejected(db_session):
    customer = create_customer(db_session)

    create_ticket(
        db_session,
        customer.id,
        ticket_number="TKT-DUP",
    )

    service = SupportTicketService()

    data = SupportTicketCreate(
        customer_id=customer.id,
        ticket_number="TKT-DUP",
        title="Duplicate ticket",
        description="Duplicate ticket number test",
        category=TicketCategory.TECHNICAL,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_ticket(
            db_session,
            data,
        )

    assert exc.value.status_code == 409


def test_invalid_customer_rejected(db_session):
    service = SupportTicketService()

    data = SupportTicketCreate(
        customer_id=99999,
        ticket_number="TKT-NOCUSTOMER",
        title="Test ticket",
        description="Customer does not exist",
        category=TicketCategory.ACCOUNT,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_ticket(
            db_session,
            data,
        )

    assert exc.value.status_code == 404


def test_invalid_outage_rejected(db_session):
    customer = create_customer(db_session)

    service = SupportTicketService()

    data = SupportTicketCreate(
        customer_id=customer.id,
        outage_id=99999,
        ticket_number="TKT-NOOUTAGE",
        title="Network problem",
        description="Referenced outage does not exist",
        category=TicketCategory.NETWORK,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_ticket(
            db_session,
            data,
        )

    assert exc.value.status_code == 404


def test_ticket_can_link_to_outage(db_session):
    customer = create_customer(db_session)
    outage = create_outage(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
        ticket_number="TKT-OUTAGE",
        outage_id=outage.id,
    )

    assert ticket.outage_id == outage.id


def test_update_ticket(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    data = SupportTicketUpdate(
        title="Updated network issue",
        priority=TicketPriority.CRITICAL,
    )

    updated = service.update_ticket(
        db_session,
        ticket.id,
        data,
    )

    assert updated.title == "Updated network issue"
    assert updated.priority == TicketPriority.CRITICAL


def test_open_to_in_progress(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    updated = service.update_status(
        db_session,
        ticket.id,
        TicketStatusUpdate(
            status=TicketStatus.IN_PROGRESS,
        ),
    )

    assert updated.status == TicketStatus.IN_PROGRESS


def test_invalid_status_transition_rejected(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            db_session,
            ticket.id,
            TicketStatusUpdate(
                status=TicketStatus.CLOSED,
            ),
        )

    assert exc.value.status_code == 400


def test_resolve_ticket(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    service.update_status(
        db_session,
        ticket.id,
        TicketStatusUpdate(
            status=TicketStatus.IN_PROGRESS,
        ),
    )

    resolved = service.resolve_ticket(
        db_session,
        ticket.id,
        TicketResolution(
            resolution_notes="Network configuration corrected",
        ),
    )

    assert resolved.status == TicketStatus.RESOLVED
    assert resolved.resolution_notes == (
        "Network configuration corrected"
    )
    assert resolved.resolved_at is not None


def test_resolved_ticket_can_be_closed(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    service.resolve_ticket(
        db_session,
        ticket.id,
        TicketResolution(
            resolution_notes="Issue fixed",
        ),
    )

    closed = service.update_status(
        db_session,
        ticket.id,
        TicketStatusUpdate(
            status=TicketStatus.CLOSED,
        ),
    )

    assert closed.status == TicketStatus.CLOSED
    assert closed.closed_at is not None


def test_closed_ticket_cannot_be_updated(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    service.resolve_ticket(
        db_session,
        ticket.id,
        TicketResolution(
            resolution_notes="Issue fixed",
        ),
    )

    service.update_status(
        db_session,
        ticket.id,
        TicketStatusUpdate(
            status=TicketStatus.CLOSED,
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.update_ticket(
            db_session,
            ticket.id,
            SupportTicketUpdate(
                title="Should fail",
            ),
        )

    assert exc.value.status_code == 400


def test_cancel_ticket(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    cancelled = service.cancel_ticket(
        db_session,
        ticket.id,
    )

    assert cancelled.status == TicketStatus.CANCELLED
    assert cancelled.cancelled_at is not None


def test_cancelled_ticket_cannot_be_resolved(db_session):
    customer = create_customer(db_session)

    ticket = create_ticket(
        db_session,
        customer.id,
    )

    service = SupportTicketService()

    service.cancel_ticket(
        db_session,
        ticket.id,
    )

    with pytest.raises(HTTPException) as exc:
        service.resolve_ticket(
            db_session,
            ticket.id,
            TicketResolution(
                resolution_notes="Should fail",
            ),
        )

    assert exc.value.status_code == 400


def test_list_tickets(db_session):
    customer = create_customer(db_session)

    create_ticket(
        db_session,
        customer.id,
        ticket_number="TKT-LIST-001",
    )

    create_ticket(
        db_session,
        customer.id,
        ticket_number="TKT-LIST-002",
    )

    service = SupportTicketService()

    result = service.list_tickets(
        db_session,
        customer_id=customer.id,
    )

    assert result["total"] == 2
    assert len(result["items"]) == 2


def test_filter_tickets_by_priority(db_session):
    customer = create_customer(db_session)

    first = create_ticket(
        db_session,
        customer.id,
        ticket_number="TKT-PRIORITY-001",
    )

    first.priority = TicketPriority.CRITICAL
    db_session.commit()

    create_ticket(
        db_session,
        customer.id,
        ticket_number="TKT-PRIORITY-002",
    )

    service = SupportTicketService()

    result = service.list_tickets(
        db_session,
        priority=TicketPriority.CRITICAL,
    )

    assert result["total"] == 1
    assert result["items"][0].id == first.id


def test_search_tickets(db_session):
    customer = create_customer(db_session)

    create_ticket(
        db_session,
        customer.id,
        ticket_number="TKT-SEARCH-001",
    )

    service = SupportTicketService()

    result = service.list_tickets(
        db_session,
        search="No network",
    )

    assert result["total"] == 1
    assert result["items"][0].ticket_number == "TKT-SEARCH-001"