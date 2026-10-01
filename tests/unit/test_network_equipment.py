from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.network_equipment import (
    EquipmentStatus,
    EquipmentType,
)
from app.models.network_tower import (
    NetworkTower,
    TowerStatus,
    TowerType,
)
from app.schemas.network_equipment import (
    NetworkEquipmentCreate,
    NetworkEquipmentStatusUpdate,
    NetworkEquipmentUpdate,
)
from app.services.network_equipment_service import (
    NetworkEquipmentService,
)


DATABASE_URL = (
    "sqlite:///./test_network_equipment.db"
)


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()

    yield session

    session.rollback()

    for table in reversed(
        Base.metadata.sorted_tables
    ):
        session.execute(table.delete())

    session.commit()
    session.close()


def create_tower(
    db,
    code="TOWER001",
    status=TowerStatus.ACTIVE,
):
    tower = NetworkTower(
        tower_code=code,
        tower_name="Hyderabad Tower",
        tower_type=TowerType.MACRO,
        status=status,
        latitude=17.385044,
        longitude=78.486671,
        address="Main Road",
        city="Hyderabad",
        state="Telangana",
        postal_code="500001",
        coverage_radius_km=5,
        capacity=1000,
        installation_date=date.today(),
    )

    db.add(tower)
    db.commit()
    db.refresh(tower)

    return tower


def equipment_data(
    tower_id,
    code="EQ001",
    serial="SERIAL001",
):
    return NetworkEquipmentCreate(
        equipment_code=code,
        serial_number=serial,
        equipment_name="Tower BTS Equipment",
        equipment_type=EquipmentType.BTS,
        manufacturer="Ericsson",
        model_number="BTS-1000",
        tower_id=tower_id,
        capacity=500,
        installation_date=date.today(),
        warranty_expiry_date=(
            date.today()
            + timedelta(days=365)
        ),
    )


# =========================================================
# CREATE
# =========================================================


def test_create_network_equipment(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    assert equipment.id is not None
    assert equipment.equipment_code == "EQ001"
    assert equipment.serial_number == "SERIAL001"
    assert equipment.tower_id == tower.id
    assert (
        equipment.equipment_type
        == EquipmentType.BTS
    )
    assert (
        equipment.status
        == EquipmentStatus.REGISTERED
    )


def test_duplicate_equipment_code_blocked(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    service.create_equipment(
        equipment_data(tower.id)
    )

    with pytest.raises(HTTPException) as exc:
        service.create_equipment(
            equipment_data(tower.id)
        )

    assert exc.value.status_code == 409
    assert (
        "Equipment code already exists"
        in exc.value.detail
    )


def test_duplicate_serial_number_blocked(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    service.create_equipment(
        equipment_data(tower.id)
    )

    with pytest.raises(HTTPException) as exc:
        service.create_equipment(
            equipment_data(
                tower.id,
                code="EQ002",
                serial="SERIAL001",
            )
        )

    assert exc.value.status_code == 409
    assert (
        "serial number"
        in exc.value.detail
    )


# =========================================================
# TOWER VALIDATION
# =========================================================


def test_missing_tower_blocked(db):
    service = NetworkEquipmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_equipment(
            equipment_data(99999)
        )

    assert exc.value.status_code == 404
    assert (
        "Network tower not found"
        in exc.value.detail
    )


def test_decommissioned_tower_blocked(db):
    tower = create_tower(
        db,
        status=TowerStatus.DECOMMISSIONED,
    )

    service = NetworkEquipmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_equipment(
            equipment_data(tower.id)
        )

    assert exc.value.status_code == 400
    assert (
        "decommissioned tower"
        in exc.value.detail
    )


# =========================================================
# DATE VALIDATION
# =========================================================


def test_future_installation_date_blocked(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    data = equipment_data(tower.id)

    data.installation_date = (
        date.today()
        + timedelta(days=1)
    )

    with pytest.raises(HTTPException) as exc:
        service.create_equipment(data)

    assert exc.value.status_code == 400
    assert "future" in exc.value.detail


def test_invalid_warranty_date_blocked(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    data = equipment_data(tower.id)

    data.warranty_expiry_date = (
        date.today()
        - timedelta(days=1)
    )

    with pytest.raises(HTTPException) as exc:
        service.create_equipment(data)

    assert exc.value.status_code == 400
    assert (
        "Warranty expiry date"
        in exc.value.detail
    )


# =========================================================
# GET
# =========================================================


def test_get_equipment(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    result = service.get_equipment(
        equipment.id
    )

    assert result.id == equipment.id
    assert (
        result.equipment_code
        == "EQ001"
    )


def test_get_missing_equipment(db):
    service = NetworkEquipmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_equipment(99999)

    assert exc.value.status_code == 404


# =========================================================
# UPDATE
# =========================================================


def test_update_equipment(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    updated = service.update_equipment(
        equipment.id,
        NetworkEquipmentUpdate(
            equipment_name="Updated BTS",
            capacity=800,
        ),
    )

    assert (
        updated.equipment_name
        == "Updated BTS"
    )

    assert updated.capacity == 800


def test_update_equipment_tower(db):
    tower1 = create_tower(
        db,
        code="TOWER001",
    )

    tower2 = create_tower(
        db,
        code="TOWER002",
    )

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower1.id)
    )

    updated = service.update_equipment(
        equipment.id,
        NetworkEquipmentUpdate(
            tower_id=tower2.id
        ),
    )

    assert updated.tower_id == tower2.id


def test_update_to_decommissioned_tower_blocked(
    db,
):
    tower1 = create_tower(
        db,
        code="TOWER001",
    )

    tower2 = create_tower(
        db,
        code="TOWER002",
        status=TowerStatus.DECOMMISSIONED,
    )

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower1.id)
    )

    with pytest.raises(HTTPException) as exc:
        service.update_equipment(
            equipment.id,
            NetworkEquipmentUpdate(
                tower_id=tower2.id
            ),
        )

    assert exc.value.status_code == 400


def test_decommissioned_equipment_cannot_update(
    db,
):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.update_status(
        equipment.id,
        NetworkEquipmentStatusUpdate(
            status=EquipmentStatus.DECOMMISSIONED
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.update_equipment(
            equipment.id,
            NetworkEquipmentUpdate(
                equipment_name="Cannot Update"
            ),
        )

    assert exc.value.status_code == 400


def test_empty_update_blocked(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    with pytest.raises(HTTPException) as exc:
        service.update_equipment(
            equipment.id,
            NetworkEquipmentUpdate(),
        )

    assert exc.value.status_code == 400


# =========================================================
# STATUS
# =========================================================


def test_activate_equipment(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    activated = service.activate_equipment(
        equipment.id
    )

    assert (
        activated.status
        == EquipmentStatus.ACTIVE
    )


def test_active_to_maintenance(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.activate_equipment(
        equipment.id
    )

    maintenance = (
        service.put_under_maintenance(
            equipment.id
        )
    )

    assert (
        maintenance.status
        == EquipmentStatus.MAINTENANCE
    )

    assert (
        maintenance.last_maintenance_date
        == date.today()
    )


def test_maintenance_to_active(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.activate_equipment(
        equipment.id
    )

    service.put_under_maintenance(
        equipment.id
    )

    activated = service.activate_equipment(
        equipment.id
    )

    assert (
        activated.status
        == EquipmentStatus.ACTIVE
    )


def test_mark_equipment_failed(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.activate_equipment(
        equipment.id
    )

    failed = service.mark_failed(
        equipment.id
    )

    assert (
        failed.status
        == EquipmentStatus.FAILED
    )


def test_failed_to_maintenance(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.activate_equipment(
        equipment.id
    )

    service.mark_failed(
        equipment.id
    )

    maintenance = (
        service.put_under_maintenance(
            equipment.id
        )
    )

    assert (
        maintenance.status
        == EquipmentStatus.MAINTENANCE
    )


def test_deactivate_equipment(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.activate_equipment(
        equipment.id
    )

    deactivated = (
        service.deactivate_equipment(
            equipment.id
        )
    )

    assert (
        deactivated.status
        == EquipmentStatus.INACTIVE
    )


def test_invalid_status_transition(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            equipment.id,
            NetworkEquipmentStatusUpdate(
                status=EquipmentStatus.MAINTENANCE
            ),
        )

    assert exc.value.status_code == 400
    assert (
        "Invalid equipment status transition"
        in exc.value.detail
    )


def test_decommissioned_equipment_terminal(
    db,
):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.update_status(
        equipment.id,
        NetworkEquipmentStatusUpdate(
            status=EquipmentStatus.DECOMMISSIONED
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            equipment.id,
            NetworkEquipmentStatusUpdate(
                status=EquipmentStatus.ACTIVE
            ),
        )

    assert exc.value.status_code == 400


def test_cannot_activate_on_decommissioned_tower(
    db,
):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    tower.status = TowerStatus.DECOMMISSIONED
    db.commit()

    with pytest.raises(HTTPException) as exc:
        service.activate_equipment(
            equipment.id
        )

    assert exc.value.status_code == 400
    assert (
        "decommissioned tower"
        in exc.value.detail
    )


# =========================================================
# SEARCH
# =========================================================


def test_search_by_tower(db):
    tower1 = create_tower(
        db,
        code="TOWER001",
    )

    tower2 = create_tower(
        db,
        code="TOWER002",
    )

    service = NetworkEquipmentService(db)

    service.create_equipment(
        equipment_data(
            tower1.id,
            code="EQ001",
            serial="SERIAL001",
        )
    )

    service.create_equipment(
        equipment_data(
            tower2.id,
            code="EQ002",
            serial="SERIAL002",
        )
    )

    result = service.search_equipment(
        tower_id=tower1.id
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert (
        result["items"][0].tower_id
        == tower1.id
    )


def test_search_by_status(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment = service.create_equipment(
        equipment_data(tower.id)
    )

    service.activate_equipment(
        equipment.id
    )

    result = service.search_equipment(
        status=EquipmentStatus.ACTIVE
    )

    assert result["total"] == 1


def test_search_by_type(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    service.create_equipment(
        equipment_data(tower.id)
    )

    result = service.search_equipment(
        equipment_type=EquipmentType.BTS
    )

    assert result["total"] == 1


def test_search_by_text(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    service.create_equipment(
        equipment_data(tower.id)
    )

    result = service.search_equipment(
        search="Ericsson"
    )

    assert result["total"] == 1


def test_pagination(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    for number in range(1, 6):
        service.create_equipment(
            equipment_data(
                tower.id,
                code=f"EQ{number:03d}",
                serial=f"SERIAL{number:03d}",
            )
        )

    result = service.search_equipment(
        skip=0,
        limit=2,
    )

    assert result["total"] == 5
    assert len(result["items"]) == 2


def test_negative_skip_blocked(db):
    service = NetworkEquipmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.search_equipment(
            skip=-1
        )

    assert exc.value.status_code == 400


def test_invalid_limit_blocked(db):
    service = NetworkEquipmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.search_equipment(
            limit=101
        )

    assert exc.value.status_code == 400


def test_active_equipment_by_tower(db):
    tower = create_tower(db)

    service = NetworkEquipmentService(db)

    equipment1 = service.create_equipment(
        equipment_data(
            tower.id,
            code="EQ001",
            serial="SERIAL001",
        )
    )

    service.create_equipment(
        equipment_data(
            tower.id,
            code="EQ002",
            serial="SERIAL002",
        )
    )

    service.activate_equipment(
        equipment1.id
    )

    active = (
        service.get_active_equipment_by_tower(
            tower.id
        )
    )

    assert len(active) == 1
    assert (
        active[0].equipment_code
        == "EQ001"
    )