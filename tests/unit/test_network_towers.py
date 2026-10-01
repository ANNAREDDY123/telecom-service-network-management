from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.network_tower import (
    NetworkTower,
    TowerStatus,
    TowerType,
)
from app.schemas.network_tower import (
    NetworkTowerCreate,
    NetworkTowerStatusUpdate,
    NetworkTowerUpdate,
)
from app.services.network_tower_service import (
    NetworkTowerService,
)


DATABASE_URL = "sqlite:///./test_network_towers.db"


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


def tower_data(
    code="TWR001",
    name="Hyderabad Tower",
):
    return NetworkTowerCreate(
        tower_code=code,
        tower_name=name,
        tower_type=TowerType.MACRO,
        latitude=Decimal("17.385044"),
        longitude=Decimal("78.486671"),
        address="Main Road",
        city="Hyderabad",
        state="Telangana",
        postal_code="500001",
        coverage_radius_km=Decimal("5.00"),
        capacity=1000,
        installation_date=date.today(),
    )


# =========================================================
# CREATE
# =========================================================


def test_create_network_tower(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    assert tower.id is not None
    assert tower.tower_code == "TWR001"
    assert tower.tower_name == "Hyderabad Tower"
    assert tower.tower_type == TowerType.MACRO
    assert tower.status == TowerStatus.PLANNED
    assert tower.city == "Hyderabad"
    assert tower.capacity == 1000


def test_duplicate_tower_code_blocked(db):
    service = NetworkTowerService(db)

    service.create_tower(
        tower_data()
    )

    with pytest.raises(HTTPException) as exc:
        service.create_tower(
            tower_data()
        )

    assert exc.value.status_code == 409
    assert (
        "Tower code already exists"
        in exc.value.detail
    )


# =========================================================
# VALIDATION
# =========================================================


def test_invalid_latitude_blocked():
    with pytest.raises(ValueError):
        NetworkTowerCreate(
            tower_code="TWR002",
            tower_name="Invalid Tower",
            tower_type=TowerType.MICRO,
            latitude=Decimal("100"),
            longitude=Decimal("78"),
            address="Test Address",
            city="Hyderabad",
            state="Telangana",
            postal_code="500001",
            coverage_radius_km=Decimal("5"),
            capacity=100,
        )


def test_invalid_longitude_blocked():
    with pytest.raises(ValueError):
        NetworkTowerCreate(
            tower_code="TWR003",
            tower_name="Invalid Tower",
            tower_type=TowerType.MICRO,
            latitude=Decimal("17"),
            longitude=Decimal("200"),
            address="Test Address",
            city="Hyderabad",
            state="Telangana",
            postal_code="500001",
            coverage_radius_km=Decimal("5"),
            capacity=100,
        )


def test_zero_coverage_radius_blocked():
    with pytest.raises(ValueError):
        NetworkTowerCreate(
            tower_code="TWR004",
            tower_name="Invalid Tower",
            tower_type=TowerType.MICRO,
            latitude=Decimal("17"),
            longitude=Decimal("78"),
            address="Test Address",
            city="Hyderabad",
            state="Telangana",
            postal_code="500001",
            coverage_radius_km=Decimal("0"),
            capacity=100,
        )


def test_zero_capacity_blocked():
    with pytest.raises(ValueError):
        NetworkTowerCreate(
            tower_code="TWR005",
            tower_name="Invalid Tower",
            tower_type=TowerType.MICRO,
            latitude=Decimal("17"),
            longitude=Decimal("78"),
            address="Test Address",
            city="Hyderabad",
            state="Telangana",
            postal_code="500001",
            coverage_radius_km=Decimal("5"),
            capacity=0,
        )


def test_future_installation_date_blocked(db):
    service = NetworkTowerService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_tower(
            NetworkTowerCreate(
                tower_code="TWR006",
                tower_name="Future Tower",
                tower_type=TowerType.MACRO,
                latitude=Decimal("17"),
                longitude=Decimal("78"),
                address="Test Address",
                city="Hyderabad",
                state="Telangana",
                postal_code="500001",
                coverage_radius_km=Decimal("5"),
                capacity=100,
                installation_date=(
                    date.today()
                    + timedelta(days=1)
                ),
            )
        )

    assert exc.value.status_code == 400
    assert "future" in exc.value.detail


# =========================================================
# GET
# =========================================================


def test_get_network_tower(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    result = service.get_tower(
        tower.id
    )

    assert result.id == tower.id
    assert result.tower_code == "TWR001"


def test_get_missing_tower(db):
    service = NetworkTowerService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_tower(99999)

    assert exc.value.status_code == 404


# =========================================================
# UPDATE
# =========================================================


def test_update_network_tower(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    updated = service.update_tower(
        tower.id,
        NetworkTowerUpdate(
            tower_name="Updated Hyderabad Tower",
            capacity=1500,
        ),
    )

    assert (
        updated.tower_name
        == "Updated Hyderabad Tower"
    )

    assert updated.capacity == 1500


def test_decommissioned_tower_cannot_update(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    service.update_status(
        tower.id,
        NetworkTowerStatusUpdate(
            status=TowerStatus.DECOMMISSIONED
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.update_tower(
            tower.id,
            NetworkTowerUpdate(
                tower_name="Cannot Update"
            ),
        )

    assert exc.value.status_code == 400


def test_empty_update_blocked(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    with pytest.raises(HTTPException) as exc:
        service.update_tower(
            tower.id,
            NetworkTowerUpdate(),
        )

    assert exc.value.status_code == 400


# =========================================================
# STATUS TRANSITIONS
# =========================================================


def test_activate_tower(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    activated = service.activate_tower(
        tower.id
    )

    assert (
        activated.status
        == TowerStatus.ACTIVE
    )


def test_active_to_maintenance(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    service.activate_tower(
        tower.id
    )

    maintenance = (
        service.put_under_maintenance(
            tower.id
        )
    )

    assert (
        maintenance.status
        == TowerStatus.MAINTENANCE
    )

    assert (
        maintenance.last_maintenance_date
        == date.today()
    )


def test_maintenance_to_active(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    service.activate_tower(
        tower.id
    )

    service.put_under_maintenance(
        tower.id
    )

    activated = service.activate_tower(
        tower.id
    )

    assert (
        activated.status
        == TowerStatus.ACTIVE
    )


def test_deactivate_active_tower(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    service.activate_tower(
        tower.id
    )

    deactivated = (
        service.deactivate_tower(
            tower.id
        )
    )

    assert (
        deactivated.status
        == TowerStatus.INACTIVE
    )


def test_invalid_status_transition(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            tower.id,
            NetworkTowerStatusUpdate(
                status=TowerStatus.MAINTENANCE
            ),
        )

    assert exc.value.status_code == 400
    assert (
        "Invalid tower status transition"
        in exc.value.detail
    )


def test_decommissioned_is_terminal(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    service.update_status(
        tower.id,
        NetworkTowerStatusUpdate(
            status=TowerStatus.DECOMMISSIONED
        ),
    )

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            tower.id,
            NetworkTowerStatusUpdate(
                status=TowerStatus.ACTIVE
            ),
        )

    assert exc.value.status_code == 400


# =========================================================
# SEARCH
# =========================================================


def test_search_by_city(db):
    service = NetworkTowerService(db)

    service.create_tower(
        tower_data(
            code="TWR010",
            name="Hyderabad Macro",
        )
    )

    service.create_tower(
        NetworkTowerCreate(
            tower_code="TWR011",
            tower_name="Bengaluru Tower",
            tower_type=TowerType.MICRO,
            latitude=Decimal("12.971599"),
            longitude=Decimal("77.594566"),
            address="Bengaluru Road",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            coverage_radius_km=Decimal("3"),
            capacity=500,
        )
    )

    result = service.search_towers(
        city="Hyderabad"
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert (
        result["items"][0].city
        == "Hyderabad"
    )


def test_search_by_status(db):
    service = NetworkTowerService(db)

    tower = service.create_tower(
        tower_data()
    )

    service.activate_tower(
        tower.id
    )

    result = service.search_towers(
        status=TowerStatus.ACTIVE
    )

    assert result["total"] == 1
    assert (
        result["items"][0].status
        == TowerStatus.ACTIVE
    )


def test_search_by_type(db):
    service = NetworkTowerService(db)

    service.create_tower(
        tower_data()
    )

    result = service.search_towers(
        tower_type=TowerType.MACRO
    )

    assert result["total"] == 1


def test_search_by_text(db):
    service = NetworkTowerService(db)

    service.create_tower(
        tower_data(
            code="HYD-TOWER-001",
            name="Hyderabad Central Tower",
        )
    )

    result = service.search_towers(
        search="Central"
    )

    assert result["total"] == 1
    assert (
        result["items"][0].tower_name
        == "Hyderabad Central Tower"
    )


def test_pagination(db):
    service = NetworkTowerService(db)

    for number in range(1, 6):
        service.create_tower(
            tower_data(
                code=f"TWR{number:03d}",
                name=f"Tower {number}",
            )
        )

    result = service.search_towers(
        skip=0,
        limit=2,
    )

    assert result["total"] == 5
    assert len(result["items"]) == 2


def test_negative_skip_blocked(db):
    service = NetworkTowerService(db)

    with pytest.raises(HTTPException) as exc:
        service.search_towers(
            skip=-1
        )

    assert exc.value.status_code == 400


def test_invalid_limit_blocked(db):
    service = NetworkTowerService(db)

    with pytest.raises(HTTPException) as exc:
        service.search_towers(
            limit=101
        )

    assert exc.value.status_code == 400


def test_get_active_towers(db):
    service = NetworkTowerService(db)

    tower1 = service.create_tower(
        tower_data(
            code="ACTIVE001",
            name="Active Tower",
        )
    )

    service.create_tower(
        tower_data(
            code="PLANNED001",
            name="Planned Tower",
        )
    )

    service.activate_tower(
        tower1.id
    )

    active_towers = (
        service.get_active_towers()
    )

    assert len(active_towers) == 1
    assert (
        active_towers[0].tower_code
        == "ACTIVE001"
    )