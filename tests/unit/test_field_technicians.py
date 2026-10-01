from datetime import datetime

import pytest

from app.core.security import hash_password
from app.models.field_technician import (
    FieldTechnician,
    TechnicianAvailability,
    TechnicianStatus,
)
from app.models.user import User, UserRole
from app.schemas.field_technician import (
    FieldTechnicianCreate,
    FieldTechnicianUpdate,
    TechnicianAvailabilityUpdate,
    TechnicianStatusUpdate,
)
from app.services.field_technician_service import (
    FieldTechnicianService,
)


def create_user(
    db,
    email="technician@example.com",
    role=UserRole.FIELD_TECHNICIAN,
):
    phone_number = (
        "9"
        + "".join(
            str(ord(char) % 10)
            for char in email
        )
    )[:10]

    user = User(
        full_name="Test Technician",
        email=email,
        phone=phone_number,
        hashed_password=hash_password(
            "Test@12345"
        ),
        role=role,
        is_active=True,
        is_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_technician(
    db,
    code="TECH-001",
):
    user = create_user(
        db,
        email=f"{code.lower()}@example.com",
    )

    service = FieldTechnicianService(db)

    technician = service.create_technician(
        FieldTechnicianCreate(
            user_id=user.id,
            technician_code=code,
            specialization="Network Maintenance",
            skills=(
                "Fiber, BTS, Router, "
                "Network Troubleshooting"
            ),
            service_area="Hyderabad",
            city="Hyderabad",
            state="Telangana",
            joined_date=datetime.utcnow(),
        )
    )

    db.commit()

    return technician


def test_create_field_technician(db_session):
    user = create_user(db_session)

    service = FieldTechnicianService(
        db_session
    )

    technician = service.create_technician(
        FieldTechnicianCreate(
            user_id=user.id,
            technician_code="TECH-001",
            specialization="Network Maintenance",
            skills="Fiber, BTS, Router",
            service_area="Hyderabad",
            city="Hyderabad",
            state="Telangana",
            joined_date=datetime.utcnow(),
        )
    )

    db_session.commit()

    assert technician.id is not None
    assert technician.user_id == user.id
    assert technician.technician_code == "TECH-001"
    assert (
        technician.status
        == TechnicianStatus.AVAILABLE
    )
    assert (
        technician.availability
        == TechnicianAvailability.AVAILABLE
    )
    assert technician.is_active is True


def test_non_technician_user_rejected(
    db_session,
):
    user = create_user(
        db_session,
        email="customer@example.com",
        role=UserRole.CUSTOMER,
    )

    service = FieldTechnicianService(
        db_session
    )

    with pytest.raises(Exception) as exc_info:
        service.create_technician(
            FieldTechnicianCreate(
                user_id=user.id,
                technician_code="TECH-002",
                specialization="Network",
                skills="Fiber",
                service_area="Hyderabad",
                city="Hyderabad",
                state="Telangana",
            )
        )

    assert exc_info.value.status_code == 400


def test_duplicate_user_profile_rejected(
    db_session,
):
    user = create_user(db_session)

    service = FieldTechnicianService(
        db_session
    )

    service.create_technician(
        FieldTechnicianCreate(
            user_id=user.id,
            technician_code="TECH-003",
            specialization="Network",
            skills="Fiber",
            service_area="Hyderabad",
            city="Hyderabad",
            state="Telangana",
        )
    )

    with pytest.raises(Exception) as exc_info:
        service.create_technician(
            FieldTechnicianCreate(
                user_id=user.id,
                technician_code="TECH-004",
                specialization="Network",
                skills="Router",
                service_area="Hyderabad",
                city="Hyderabad",
                state="Telangana",
            )
        )

    assert exc_info.value.status_code == 409


def test_duplicate_technician_code_rejected(
    db_session,
):
    create_technician(
        db_session,
        "TECH-005",
    )

    user = create_user(
        db_session,
        email="another@example.com",
    )

    service = FieldTechnicianService(
        db_session
    )

    with pytest.raises(Exception) as exc_info:
        service.create_technician(
            FieldTechnicianCreate(
                user_id=user.id,
                technician_code="TECH-005",
                specialization="Network",
                skills="Fiber",
                service_area="Hyderabad",
                city="Hyderabad",
                state="Telangana",
            )
        )

    assert exc_info.value.status_code == 409


def test_update_technician(db_session):
    technician = create_technician(
        db_session,
        "TECH-006",
    )

    service = FieldTechnicianService(
        db_session
    )

    updated = service.update_technician(
        technician.id,
        FieldTechnicianUpdate(
            specialization="Fiber Specialist",
            skills="Fiber, Optical Network",
            service_area="Hyderabad Metro",
        ),
    )

    db_session.commit()

    assert (
        updated.specialization
        == "Fiber Specialist"
    )
    assert (
        updated.skills
        == "Fiber, Optical Network"
    )
    assert (
        updated.service_area
        == "Hyderabad Metro"
    )


def test_status_transition_available_to_busy(
    db_session,
):
    technician = create_technician(
        db_session,
        "TECH-007",
    )

    service = FieldTechnicianService(
        db_session
    )

    updated = service.update_status(
        technician.id,
        TechnicianStatusUpdate(
            status=TechnicianStatus.BUSY
        ),
    )

    db_session.commit()

    assert (
        updated.status
        == TechnicianStatus.BUSY
    )
    assert updated.is_active is True


def test_invalid_status_transition_rejected(
    db_session,
):
    technician = create_technician(
        db_session,
        "TECH-008",
    )

    service = FieldTechnicianService(
        db_session
    )

    service.update_status(
        technician.id,
        TechnicianStatusUpdate(
            status=TechnicianStatus.ON_LEAVE
        ),
    )

    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        service.update_status(
            technician.id,
            TechnicianStatusUpdate(
                status=TechnicianStatus.BUSY
            ),
        )

    assert exc_info.value.status_code == 400


def test_update_availability(
    db_session,
):
    technician = create_technician(
        db_session,
        "TECH-009",
    )

    service = FieldTechnicianService(
        db_session
    )

    updated = service.update_availability(
        technician.id,
        TechnicianAvailabilityUpdate(
            availability=(
                TechnicianAvailability.UNAVAILABLE
            )
        ),
    )

    db_session.commit()

    assert (
        updated.availability
        == TechnicianAvailability.UNAVAILABLE
    )


def test_on_leave_cannot_be_available(
    db_session,
):
    technician = create_technician(
        db_session,
        "TECH-010",
    )

    service = FieldTechnicianService(
        db_session
    )

    service.update_status(
        technician.id,
        TechnicianStatusUpdate(
            status=TechnicianStatus.ON_LEAVE
        ),
    )

    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        service.update_availability(
            technician.id,
            TechnicianAvailabilityUpdate(
                availability=(
                    TechnicianAvailability.AVAILABLE
                )
            ),
        )

    assert exc_info.value.status_code == 400


def test_deactivate_technician(
    db_session,
):
    technician = create_technician(
        db_session,
        "TECH-011",
    )

    service = FieldTechnicianService(
        db_session
    )

    updated = service.deactivate_technician(
        technician.id
    )

    db_session.commit()

    assert updated.is_active is False
    assert (
        updated.status
        == TechnicianStatus.INACTIVE
    )
    assert (
        updated.availability
        == TechnicianAvailability.UNAVAILABLE
    )


def test_activate_technician(
    db_session,
):
    technician = create_technician(
        db_session,
        "TECH-012",
    )

    service = FieldTechnicianService(
        db_session
    )

    service.deactivate_technician(
        technician.id
    )

    db_session.commit()

    updated = service.activate_technician(
        technician.id
    )

    db_session.commit()

    assert updated.is_active is True
    assert (
        updated.status
        == TechnicianStatus.AVAILABLE
    )
    assert (
        updated.availability
        == TechnicianAvailability.AVAILABLE
    )


def test_list_technicians(
    db_session,
):
    create_technician(
        db_session,
        "TECH-013",
    )

    create_technician(
        db_session,
        "TECH-014",
    )

    service = FieldTechnicianService(
        db_session
    )

    result = service.list_technicians(
        city="Hyderabad",
        page=1,
        limit=10,
    )

    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["page"] == 1


def test_get_available_technicians(
    db_session,
):
    create_technician(
        db_session,
        "TECH-015",
    )

    busy = create_technician(
        db_session,
        "TECH-016",
    )

    service = FieldTechnicianService(
        db_session
    )

    service.update_status(
        busy.id,
        TechnicianStatusUpdate(
            status=TechnicianStatus.BUSY
        ),
    )

    db_session.commit()

    available = (
        service.get_available_technicians(
            city="Hyderabad"
        )
    )

    assert len(available) == 1
    assert (
        available[0].technician_code
        == "TECH-015"
    )


def test_inactive_technician_cannot_update(
    db_session,
):
    technician = create_technician(
        db_session,
        "TECH-017",
    )

    service = FieldTechnicianService(
        db_session
    )

    service.deactivate_technician(
        technician.id
    )

    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        service.update_technician(
            technician.id,
            FieldTechnicianUpdate(
                specialization="Updated",
            ),
        )

    assert exc_info.value.status_code == 400