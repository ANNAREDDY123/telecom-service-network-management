from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.customer import Customer
from app.models.service_plan import (
    PlanStatus,
    PlanType,
    ServicePlan,
    ServiceType,
)
from app.models.sim_card import (
    SIMCard,
    SIMStatus,
    SIMType,
)
from app.services.sim_card_service import SIMCardService
from app.schemas.sim_card import (
    SIMCardCreate,
    SIMReplacementCreate,
)


DATABASE_URL = "sqlite:///./test_sim_cards.db"

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

    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())

    session.commit()
    session.close()


def create_customer(db):
    customer = Customer(
        user_id=1,
        customer_number="CUS001",
        full_name="Test Customer",
        email="test@example.com",
        phone="9876543210",
        is_active=True,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_plan(db):
    plan = ServicePlan(
        plan_code="PLAN001",
        plan_name="Test Plan",
        description="Test service plan",
        plan_type=PlanType.POSTPAID,
        service_type=ServiceType.DATA,
        price=499,
        validity_days=30,
        data_limit_mb=10000,
        status=PlanStatus.ACTIVE,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


def test_create_available_sim(db):
    service = SIMCardService(db)

    sim = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456789",
            sim_type=SIMType.PHYSICAL,
        )
    )

    assert sim.id is not None
    assert sim.sim_number == "SIM123456789"
    assert sim.sim_type == SIMType.PHYSICAL
    assert sim.status == SIMStatus.AVAILABLE
    assert sim.customer_id is None
    assert sim.plan_id is None


def test_create_sim_for_customer_requires_plan(db):
    customer = create_customer(db)

    service = SIMCardService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_sim(
            SIMCardCreate(
                sim_number="SIM123456790",
                sim_type=SIMType.PHYSICAL,
                customer_id=customer.id,
            )
        )

    assert exc.value.status_code == 400
    assert "service plan is required" in exc.value.detail


def test_create_sim_with_customer_and_plan(db):
    customer = create_customer(db)
    plan = create_plan(db)

    service = SIMCardService(db)

    sim = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456791",
            sim_type=SIMType.ESIM,
            customer_id=customer.id,
            plan_id=plan.id,
        )
    )

    assert sim.status == SIMStatus.AVAILABLE
    assert sim.customer_id == customer.id
    assert sim.plan_id == plan.id


def test_duplicate_sim_number_blocked(db):
    service = SIMCardService(db)

    service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456792",
            sim_type=SIMType.PHYSICAL,
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.create_sim(
            SIMCardCreate(
                sim_number="SIM123456792",
                sim_type=SIMType.ESIM,
            )
        )

    assert exc.value.status_code == 409


def test_activate_sim(db):
    customer = create_customer(db)
    plan = create_plan(db)

    service = SIMCardService(db)

    sim = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456793",
            sim_type=SIMType.PHYSICAL,
            customer_id=customer.id,
            plan_id=plan.id,
        )
    )

    activated = service.activate_sim(sim.id)

    assert activated.status == SIMStatus.ACTIVE
    assert activated.activation_date == date.today()


def test_activation_requires_customer(db):
    plan = create_plan(db)

    service = SIMCardService(db)

    sim = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456794",
            sim_type=SIMType.PHYSICAL,
            plan_id=plan.id,
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.activate_sim(sim.id)

    assert exc.value.status_code == 400
    assert "customer" in exc.value.detail.lower()


def test_only_one_active_sim_per_customer(db):
    customer = create_customer(db)
    plan = create_plan(db)

    service = SIMCardService(db)

    sim1 = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456795",
            sim_type=SIMType.PHYSICAL,
            customer_id=customer.id,
            plan_id=plan.id,
        )
    )

    sim2 = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456796",
            sim_type=SIMType.ESIM,
            customer_id=customer.id,
            plan_id=plan.id,
        )
    )

    service.activate_sim(sim1.id)

    with pytest.raises(HTTPException) as exc:
        service.activate_sim(sim2.id)

    assert exc.value.status_code == 409


def test_invalid_status_transition_blocked(db):
    service = SIMCardService(db)

    sim = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456797",
            sim_type=SIMType.PHYSICAL,
        )
    )

    sim.status = SIMStatus.DEACTIVATED
    db.commit()

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            sim.id,
            type(
                "StatusData",
                (),
                {"status": SIMStatus.ACTIVE},
            )(),
        )

    assert exc.value.status_code == 400


def test_replace_sim(db):
    customer = create_customer(db)
    plan = create_plan(db)

    service = SIMCardService(db)

    old_sim = service.create_sim(
        SIMCardCreate(
            sim_number="SIM123456798",
            sim_type=SIMType.PHYSICAL,
            customer_id=customer.id,
            plan_id=plan.id,
        )
    )

    service.activate_sim(old_sim.id)

    old_sim, new_sim = service.replace_sim(
        old_sim.id,
        SIMReplacementCreate(
            new_sim_number="SIM123456799",
            sim_type=SIMType.ESIM,
            reason="SIM damaged",
        ),
    )

    assert old_sim.status == SIMStatus.DEACTIVATED
    assert new_sim.status == SIMStatus.AVAILABLE
    assert new_sim.customer_id == customer.id
    assert new_sim.plan_id == plan.id
    assert new_sim.replacement_of_sim_id == old_sim.id
    assert new_sim.replacement_reason == "SIM damaged"