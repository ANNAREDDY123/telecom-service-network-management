from datetime import datetime, timedelta

import pytest

from app.models.customer import Customer
from app.models.network_outage import (
    OutageSeverity,
    OutageStatus,
    OutageType,
)
from app.models.network_tower import (
    NetworkTower,
    TowerStatus,
    TowerType,
)
from app.models.user import User, UserRole
from app.schemas.network_outage import (
    AffectedCustomersCreate,
    OutageCreate,
    OutageRestore,
    OutageStatusUpdate,
)
from app.services.network_outage_service import (
    NetworkOutageService,
)
from app.core.security import hash_password


def create_tower(db):
    tower = NetworkTower(
        tower_code="TWR-001",
        tower_name="Test Tower",
        tower_type=TowerType.MACRO,
        status=TowerStatus.ACTIVE,
        latitude=17.3850,
        longitude=78.4867,
        address="Test Address",
        city="Hyderabad",
        state="Telangana",
        postal_code="500001",
        coverage_radius_km=5,
        capacity=1000,
        installation_date=datetime.utcnow().date(),
    )

    db.add(tower)
    db.commit()
    db.refresh(tower)

    return tower


def create_customer(
    db,
    number="CUS-001",
):
    user = User(
        full_name="Test Customer",
        email=f"{number.lower()}@example.com",
        phone=f"900000{number[-3:]}",
        hashed_password=hash_password("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
    )

    db.add(user)
    db.flush()

    customer = Customer(
        user_id=user.id,
        customer_number=number,
        full_name="Test Customer",
        email=f"{number.lower()}@example.com",
        phone=f"900000{number[-3:]}",
        is_active=True,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_outage_data(
    tower_id,
    outage_number="OUT-001",
):
    return OutageCreate(
        outage_number=outage_number,
        title="Network connectivity issue",
        description=(
            "Connectivity lost in the service area."
        ),
        outage_type=OutageType.NETWORK,
        severity=OutageSeverity.HIGH,
        tower_id=tower_id,
        start_time=(
            datetime.utcnow()
            - timedelta(minutes=30)
        ),
        expected_restore_time=(
            datetime.utcnow()
            + timedelta(hours=2)
        ),
        root_cause="Transmission failure",
    )


def test_create_outage(db_session):
    tower = create_tower(db_session)

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    assert outage.id is not None
    assert outage.outage_number == "OUT-001"
    assert outage.status == OutageStatus.REPORTED
    assert outage.tower_id == tower.id


def test_duplicate_outage_number_rejected(
    db_session,
):
    tower = create_tower(db_session)

    service = NetworkOutageService(
        db_session
    )

    service.create_outage(
        create_outage_data(tower.id)
    )

    with pytest.raises(Exception) as exc_info:
        service.create_outage(
            create_outage_data(tower.id)
        )

    assert exc_info.value.status_code == 409


def test_future_outage_start_rejected(
    db_session,
):
    tower = create_tower(db_session)

    service = NetworkOutageService(
        db_session
    )

    data = OutageCreate(
        outage_number="OUT-002",
        title="Future outage",
        outage_type=OutageType.NETWORK,
        severity=OutageSeverity.MEDIUM,
        tower_id=tower.id,
        start_time=(
            datetime.utcnow()
            + timedelta(hours=1)
        ),
    )

    with pytest.raises(Exception) as exc_info:
        service.create_outage(data)

    assert exc_info.value.status_code == 400


def test_decommissioned_tower_rejected(
    db_session,
):
    tower = create_tower(db_session)

    tower.status = (
        TowerStatus.DECOMMISSIONED
    )

    db_session.commit()

    service = NetworkOutageService(
        db_session
    )

    with pytest.raises(Exception) as exc_info:
        service.create_outage(
            create_outage_data(tower.id)
        )

    assert exc_info.value.status_code == 400


def test_invalid_status_transition_rejected(
    db_session,
):
    tower = create_tower(db_session)

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    with pytest.raises(Exception) as exc_info:
        service.update_status(
            outage.id,
            OutageStatusUpdate(
                status=OutageStatus.CLOSED
            ),
        )

    assert exc_info.value.status_code == 400


def test_identify_affected_customers(
    db_session,
):
    tower = create_tower(db_session)

    customer1 = create_customer(
        db_session,
        "CUS-001",
    )

    customer2 = create_customer(
        db_session,
        "CUS-002",
    )

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    affected = (
        service.identify_affected_customers(
            outage.id,
            AffectedCustomersCreate(
                customer_ids=[
                    customer1.id,
                    customer2.id,
                ]
            ),
        )
    )

    assert len(affected) == 2

    refreshed = service.get_outage(
        outage.id
    )

    assert (
        refreshed.affected_customer_count
        == 2
    )


def test_duplicate_affected_customer_rejected(
    db_session,
):
    tower = create_tower(db_session)

    customer = create_customer(
        db_session,
        "CUS-003",
    )

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    data = AffectedCustomersCreate(
        customer_ids=[customer.id]
    )

    service.identify_affected_customers(
        outage.id,
        data,
    )

    with pytest.raises(Exception) as exc_info:
        service.identify_affected_customers(
            outage.id,
            data,
        )

    assert exc_info.value.status_code == 409


def test_restore_outage(db_session):
    tower = create_tower(db_session)

    customer = create_customer(
        db_session,
        "CUS-004",
    )

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    service.identify_affected_customers(
        outage.id,
        AffectedCustomersCreate(
            customer_ids=[customer.id]
        ),
    )

    service.update_status(
        outage.id,
        OutageStatusUpdate(
            status=OutageStatus.INVESTIGATING
        ),
    )

    service.update_status(
        outage.id,
        OutageStatusUpdate(
            status=OutageStatus.IN_PROGRESS
        ),
    )

    restored = service.restore_outage(
        outage.id,
        OutageRestore(
            resolution_notes=(
                "Network restored successfully."
            )
        ),
    )

    assert (
        restored.status
        == OutageStatus.RESTORED
    )

    assert (
        restored.actual_restore_time
        is not None
    )


def test_close_only_restored_outage(
    db_session,
):
    tower = create_tower(db_session)

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    with pytest.raises(Exception) as exc_info:
        service.close_outage(
            outage.id
        )

    assert exc_info.value.status_code == 400


def test_active_outages(db_session):
    tower = create_tower(db_session)

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    active = service.get_active_outages(
        tower_id=tower.id
    )

    assert len(active) == 1
    assert active[0].id == outage.id


def test_outage_summary(db_session):
    tower = create_tower(db_session)

    service = NetworkOutageService(
        db_session
    )

    outage = service.create_outage(
        create_outage_data(tower.id)
    )

    summary = service.get_outage_summary(
        outage.id
    )

    assert (
        summary["outage_id"]
        == outage.id
    )

    assert (
        summary["outage_number"]
        == "OUT-001"
    )

    assert (
        summary["affected_customer_count"]
        == 0
    )

    assert (
        summary["duration_minutes"]
        is not None
    )