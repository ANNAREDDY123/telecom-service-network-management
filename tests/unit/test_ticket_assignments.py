from datetime import datetime

import pytest
from fastapi import HTTPException

from app.models.customer import Customer
from app.models.field_technician import (
    FieldTechnician,
    TechnicianAvailability,
    TechnicianStatus,
)
from app.models.support_ticket import (
    SupportTicket,
    TicketCategory,
    TicketPriority,
    TicketSource,
    TicketStatus,
)
from app.models.ticket_assignment import (
    AssignmentStatus,
    AssignmentType,
    TicketAssignment,
)
from app.models.user import User, UserRole
from app.services.ticket_assignment_service import (
    TicketAssignmentService,
)
from app.schemas.ticket_assignment import (
    AssignmentStatusUpdate,
    TicketAssignmentCreate,
    TicketAssignmentUpdate,
)


_user_counter = 0
_customer_counter = 0
_ticket_counter = 0
_technician_counter = 0


def create_user(
    db_session,
    *,
    role=UserRole.CUSTOMER,
    is_active=True,
):
    global _user_counter

    _user_counter += 1

    user = User(
        full_name=f"Test User {_user_counter}",
        email=f"assignment_user_{_user_counter}@example.com",
        phone=f"910000{_user_counter:04d}",
        hashed_password="hashed-password",
        role=role,
        is_active=is_active,
        is_verified=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def create_customer(db_session, *, is_active=True):
    global _customer_counter

    _customer_counter += 1

    user = create_user(
        db_session,
        role=UserRole.CUSTOMER,
        is_active=True,
    )

    customer = Customer(
        user_id=user.id,
        customer_number=f"CUST-ASSIGN-{_customer_counter:04d}",
        full_name=f"Test Customer {_customer_counter}",
        email=f"customer_assignment_{_customer_counter}@example.com",
        phone=f"920000{_customer_counter:04d}",
        kyc_status="Pending",
        is_active=is_active,
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    return customer


def create_ticket(db_session, *, customer_id=None):
    global _ticket_counter

    _ticket_counter += 1

    if customer_id is None:
        customer = create_customer(db_session)
        customer_id = customer.id

    ticket = SupportTicket(
        ticket_number=f"TKT-ASSIGN-{_ticket_counter:04d}",
        customer_id=customer_id,
        title=f"Assignment Test Ticket {_ticket_counter}",
        description="Test ticket for Level 13 assignment testing",
        category=TicketCategory.TECHNICAL,
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
        source=TicketSource.PORTAL,
    )

    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)

    return ticket


def create_support_agent(db_session, *, is_active=True):
    return create_user(
        db_session,
        role=UserRole.SUPPORT_AGENT,
        is_active=is_active,
    )


def create_field_technician(
    db_session,
    *,
    status=TechnicianStatus.AVAILABLE,
    availability=TechnicianAvailability.AVAILABLE,
    is_active=True,
):
    global _technician_counter

    _technician_counter += 1

    user = create_user(
        db_session,
        role=UserRole.FIELD_TECHNICIAN,
        is_active=True,
    )

    technician = FieldTechnician(
        user_id=user.id,
        technician_code=f"TECH-ASSIGN-{_technician_counter:04d}",
        specialization="Network Operations",
        skills="Fiber, BTS, Router",
        service_area="Hyderabad",
        city="Hyderabad",
        state="Telangana",
        status=status,
        availability=availability,
        is_active=is_active,
        joined_date=datetime.utcnow(),
        notes="Level 13 test technician",
    )

    db_session.add(technician)
    db_session.commit()
    db_session.refresh(technician)

    return user, technician


@pytest.fixture
def service():
    return TicketAssignmentService()


# -------------------------------------------------------------------------
# CREATE ASSIGNMENT
# -------------------------------------------------------------------------


def test_support_agent_can_be_assigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=agent.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
        notes="Assigned to support agent",
    )

    assignment = service.create_assignment(
        db_session,
        data,
    )

    assert assignment.id is not None
    assert assignment.ticket_id == ticket.id
    assert assignment.assigned_user_id == agent.id
    assert assignment.assignment_type == AssignmentType.SUPPORT_AGENT
    assert assignment.status == AssignmentStatus.ASSIGNED
    assert assignment.notes == "Assigned to support agent"


def test_field_technician_can_be_assigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    technician_user, technician = create_field_technician(
        db_session,
    )

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=technician_user.id,
        assignment_type=AssignmentType.FIELD_TECHNICIAN,
        notes="Field technician assignment",
    )

    assignment = service.create_assignment(
        db_session,
        data,
    )

    assert assignment.id is not None
    assert assignment.assigned_user_id == technician_user.id
    assert assignment.assignment_type == AssignmentType.FIELD_TECHNICIAN
    assert assignment.status == AssignmentStatus.ASSIGNED


def test_invalid_support_agent_role_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    customer_user = create_user(
        db_session,
        role=UserRole.CUSTOMER,
    )

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=customer_user.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400
    assert "Support Agent role" in exc.value.detail


def test_invalid_field_technician_role_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=agent.id,
        assignment_type=AssignmentType.FIELD_TECHNICIAN,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400
    assert "Field Technician role" in exc.value.detail


def test_inactive_user_cannot_be_assigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    inactive_agent = create_support_agent(
        db_session,
        is_active=False,
    )

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=inactive_agent.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400
    assert "Inactive user" in exc.value.detail


# -------------------------------------------------------------------------
# FIELD TECHNICIAN VALIDATION
# -------------------------------------------------------------------------


def test_field_technician_without_profile_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    technician_user = create_user(
        db_session,
        role=UserRole.FIELD_TECHNICIAN,
    )

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=technician_user.id,
        assignment_type=AssignmentType.FIELD_TECHNICIAN,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 404
    assert "profile not found" in exc.value.detail


def test_unavailable_field_technician_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    technician_user, technician = create_field_technician(
        db_session,
        status=TechnicianStatus.BUSY,
        availability=TechnicianAvailability.AVAILABLE,
    )

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=technician_user.id,
        assignment_type=AssignmentType.FIELD_TECHNICIAN,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400
    assert "not available" in exc.value.detail


def test_unavailable_technician_availability_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    technician_user, technician = create_field_technician(
        db_session,
        status=TechnicianStatus.AVAILABLE,
        availability=TechnicianAvailability.UNAVAILABLE,
    )

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=technician_user.id,
        assignment_type=AssignmentType.FIELD_TECHNICIAN,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400
    assert "currently unavailable" in exc.value.detail


def test_inactive_field_technician_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    technician_user, technician = create_field_technician(
        db_session,
        status=TechnicianStatus.AVAILABLE,
        availability=TechnicianAvailability.AVAILABLE,
        is_active=False,
    )

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=technician_user.id,
        assignment_type=AssignmentType.FIELD_TECHNICIAN,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400
    assert "Inactive field technician" in exc.value.detail


# -------------------------------------------------------------------------
# TICKET VALIDATION
# -------------------------------------------------------------------------


def test_invalid_ticket_rejected(
    db_session,
    service,
):
    agent = create_support_agent(db_session)

    data = TicketAssignmentCreate(
        ticket_id=999999,
        assigned_user_id=agent.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 404
    assert "Support ticket not found" in exc.value.detail


def test_closed_ticket_cannot_be_assigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    ticket.status = TicketStatus.CLOSED

    db_session.commit()
    db_session.refresh(ticket)

    agent = create_support_agent(db_session)

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=agent.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400
    assert "cannot be assigned" in exc.value.detail


def test_cancelled_ticket_cannot_be_assigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    ticket.status = TicketStatus.CANCELLED

    db_session.commit()
    db_session.refresh(ticket)

    agent = create_support_agent(db_session)

    data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=agent.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            data,
        )

    assert exc.value.status_code == 400


# -------------------------------------------------------------------------
# DUPLICATE ACTIVE ASSIGNMENT
# -------------------------------------------------------------------------


def test_duplicate_active_assignment_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    first_data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=agent_one.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
    )

    first = service.create_assignment(
        db_session,
        first_data,
    )

    assert first.status == AssignmentStatus.ASSIGNED

    second_data = TicketAssignmentCreate(
        ticket_id=ticket.id,
        assigned_user_id=agent_two.id,
        assignment_type=AssignmentType.SUPPORT_AGENT,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_assignment(
            db_session,
            second_data,
        )

    assert exc.value.status_code == 409
    assert "active assignment" in exc.value.detail


# -------------------------------------------------------------------------
# ASSIGNMENT STATUS TRANSITIONS
# -------------------------------------------------------------------------


def test_assignment_status_assigned_to_accepted(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    updated = service.update_status(
        db_session,
        assignment.id,
        AssignmentStatusUpdate(
            status=AssignmentStatus.ACCEPTED,
        ),
    )

    assert updated.status == AssignmentStatus.ACCEPTED
    assert updated.accepted_at is not None


def test_assignment_status_accepted_to_in_progress(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    service.update_status(
        db_session,
        assignment.id,
        AssignmentStatusUpdate(
            status=AssignmentStatus.ACCEPTED,
        ),
    )

    updated = service.update_status(
        db_session,
        assignment.id,
        AssignmentStatusUpdate(
            status=AssignmentStatus.IN_PROGRESS,
        ),
    )

    assert updated.status == AssignmentStatus.IN_PROGRESS
    assert updated.started_at is not None


def test_assignment_can_be_completed(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    service.update_status(
        db_session,
        assignment.id,
        AssignmentStatusUpdate(
            status=AssignmentStatus.IN_PROGRESS,
        ),
    )

    completed = service.update_status(
        db_session,
        assignment.id,
        AssignmentStatusUpdate(
            status=AssignmentStatus.COMPLETED,
        ),
    )

    assert completed.status == AssignmentStatus.COMPLETED
    assert completed.completed_at is not None


def test_invalid_assignment_status_transition_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            db_session,
            assignment.id,
            AssignmentStatusUpdate(
                status=AssignmentStatus.COMPLETED,
            ),
        )

    assert exc.value.status_code == 400
    assert "Invalid assignment status transition" in exc.value.detail


def test_same_assignment_status_rejected(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            db_session,
            assignment.id,
            AssignmentStatusUpdate(
                status=AssignmentStatus.ASSIGNED,
            ),
        )

    assert exc.value.status_code == 400
    assert "already in the requested status" in exc.value.detail


# -------------------------------------------------------------------------
# UPDATE ASSIGNMENT
# -------------------------------------------------------------------------


def test_assignment_notes_can_be_updated(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
            notes="Initial note",
        ),
    )

    updated = service.update_assignment(
        db_session,
        assignment.id,
        TicketAssignmentUpdate(
            notes="Updated assignment note",
        ),
    )

    assert updated.notes == "Updated assignment note"


# -------------------------------------------------------------------------
# UNASSIGNMENT
# -------------------------------------------------------------------------


def test_assignment_can_be_unassigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    unassigned = service.unassign(
        db_session,
        assignment.id,
    )

    assert unassigned.status == AssignmentStatus.UNASSIGNED
    assert unassigned.unassigned_at is not None


def test_unassigned_ticket_can_be_assigned_again(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    first = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent_one.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    service.unassign(
        db_session,
        first.id,
    )

    second = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent_two.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    assert second.id != first.id
    assert second.status == AssignmentStatus.ASSIGNED
    assert second.assigned_user_id == agent_two.id


# -------------------------------------------------------------------------
# REASSIGNMENT
# -------------------------------------------------------------------------


def test_ticket_can_be_reassigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    first = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent_one.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    second = service.reassign(
        db_session,
        first.id,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent_two.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
            notes="Reassigned to another support agent",
        ),
    )

    db_session.refresh(first)

    assert first.status == AssignmentStatus.REASSIGNED
    assert first.unassigned_at is not None

    assert second.id != first.id
    assert second.ticket_id == ticket.id
    assert second.assigned_user_id == agent_two.id
    assert second.status == AssignmentStatus.ASSIGNED


def test_reassignment_requires_same_ticket(
    db_session,
    service,
):
    ticket_one = create_ticket(db_session)
    ticket_two = create_ticket(db_session)

    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    first = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket_one.id,
            assigned_user_id=agent_one.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.reassign(
            db_session,
            first.id,
            TicketAssignmentCreate(
                ticket_id=ticket_two.id,
                assigned_user_id=agent_two.id,
                assignment_type=AssignmentType.SUPPORT_AGENT,
            ),
        )

    assert exc.value.status_code == 400
    assert "ticket ID must match" in exc.value.detail


def test_completed_assignment_cannot_be_reassigned(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    first = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent_one.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    service.update_status(
        db_session,
        first.id,
        AssignmentStatusUpdate(
            status=AssignmentStatus.IN_PROGRESS,
        ),
    )

    service.update_status(
        db_session,
        first.id,
        AssignmentStatusUpdate(
            status=AssignmentStatus.COMPLETED,
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.reassign(
            db_session,
            first.id,
            TicketAssignmentCreate(
                ticket_id=ticket.id,
                assigned_user_id=agent_two.id,
                assignment_type=AssignmentType.SUPPORT_AGENT,
            ),
        )

    assert exc.value.status_code == 400
    assert "active assignment" in exc.value.detail


# -------------------------------------------------------------------------
# ASSIGNMENT HISTORY
# -------------------------------------------------------------------------


def test_assignment_history_is_preserved_after_reassignment(
    db_session,
    service,
):
    ticket = create_ticket(db_session)

    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    first = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent_one.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    second = service.reassign(
        db_session,
        first.id,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent_two.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    history = (
        db_session.query(TicketAssignment)
        .filter(
            TicketAssignment.ticket_id == ticket.id
        )
        .order_by(TicketAssignment.id.asc())
        .all()
    )

    assert len(history) == 2

    assert history[0].id == first.id
    assert history[0].status == AssignmentStatus.REASSIGNED

    assert history[1].id == second.id
    assert history[1].status == AssignmentStatus.ASSIGNED


def test_unassignment_preserves_assignment_history(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    service.unassign(
        db_session,
        assignment.id,
    )

    history = (
        db_session.query(TicketAssignment)
        .filter(
            TicketAssignment.ticket_id == ticket.id
        )
        .all()
    )

    assert len(history) == 1
    assert history[0].id == assignment.id
    assert history[0].status == AssignmentStatus.UNASSIGNED
    assert history[0].unassigned_at is not None


# -------------------------------------------------------------------------
# GET / LIST / PAGINATION
# -------------------------------------------------------------------------


def test_get_assignment(
    db_session,
    service,
):
    ticket = create_ticket(db_session)
    agent = create_support_agent(db_session)

    assignment = service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket.id,
            assigned_user_id=agent.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    result = service.get_assignment(
        db_session,
        assignment.id,
    )

    assert result.id == assignment.id
    assert result.ticket_id == ticket.id


def test_missing_assignment_returns_404(
    db_session,
    service,
):
    with pytest.raises(HTTPException) as exc:
        service.get_assignment(
            db_session,
            999999,
        )

    assert exc.value.status_code == 404


def test_list_assignments_pagination(
    db_session,
    service,
):
    agent = create_support_agent(db_session)

    for _ in range(5):
        ticket = create_ticket(db_session)

        service.create_assignment(
            db_session,
            TicketAssignmentCreate(
                ticket_id=ticket.id,
                assigned_user_id=agent.id,
                assignment_type=AssignmentType.SUPPORT_AGENT,
            ),
        )

        # End the assignment so the same agent can be used
        # for the next ticket without affecting history.
        assignment = (
            db_session.query(TicketAssignment)
            .filter(
                TicketAssignment.ticket_id == ticket.id
            )
            .first()
        )

        service.unassign(
            db_session,
            assignment.id,
        )

    result = service.list_assignments(
        db_session,
        page=1,
        limit=2,
    )

    assert result["total"] == 5
    assert len(result["items"]) == 2
    assert result["page"] == 1
    assert result["limit"] == 2
    assert result["pages"] == 3


def test_list_assignments_filter_by_user(
    db_session,
    service,
):
    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    ticket_one = create_ticket(db_session)
    ticket_two = create_ticket(db_session)

    service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket_one.id,
            assigned_user_id=agent_one.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket_two.id,
            assigned_user_id=agent_two.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    result = service.list_assignments(
        db_session,
        assigned_user_id=agent_one.id,
        page=1,
        limit=20,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].assigned_user_id == agent_one.id


def test_list_assignments_filter_by_ticket(
    db_session,
    service,
):
    ticket_one = create_ticket(db_session)
    ticket_two = create_ticket(db_session)

    agent_one = create_support_agent(db_session)
    agent_two = create_support_agent(db_session)

    service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket_one.id,
            assigned_user_id=agent_one.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    service.create_assignment(
        db_session,
        TicketAssignmentCreate(
            ticket_id=ticket_two.id,
            assigned_user_id=agent_two.id,
            assignment_type=AssignmentType.SUPPORT_AGENT,
        ),
    )

    result = service.list_assignments(
        db_session,
        ticket_id=ticket_one.id,
        page=1,
        limit=20,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].ticket_id == ticket_one.id


def test_invalid_page_rejected(
    db_session,
    service,
):
    with pytest.raises(HTTPException) as exc:
        service.list_assignments(
            db_session,
            page=0,
            limit=20,
        )

    assert exc.value.status_code == 400


def test_invalid_limit_rejected(
    db_session,
    service,
):
    with pytest.raises(HTTPException) as exc:
        service.list_assignments(
            db_session,
            page=1,
            limit=101,
        )

    assert exc.value.status_code == 400