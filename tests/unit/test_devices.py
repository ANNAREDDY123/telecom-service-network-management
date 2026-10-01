from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.customer import Customer
from app.models.device import (
    Device,
    DeviceStatus,
    DeviceType,
)
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
from app.schemas.device import (
    DeviceCreate,
    DeviceReplacementCreate,
)
from app.services.device_service import DeviceService


DATABASE_URL = "sqlite:///./test_devices.db"

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


def create_customer(db):
    customer = Customer(
        user_id=1,
        customer_number="CUS001",
        full_name="Test Customer",
        email="device-test@example.com",
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
        description="Test plan",
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


def create_active_sim(
    db,
    customer,
    plan,
    sim_number="SIM123456789",
):
    sim = SIMCard(
        sim_number=sim_number,
        sim_type=SIMType.PHYSICAL,
        status=SIMStatus.ACTIVE,
        activation_date=datetime.now(
            timezone.utc
        ).date(),
        customer_id=customer.id,
        plan_id=plan.id,
    )

    db.add(sim)
    db.commit()
    db.refresh(sim)

    return sim


def create_device(
    db,
    customer_id=None,
    sim_id=None,
    imei="123456789012345",
):
    service = DeviceService(db)

    return service.create_device(
        DeviceCreate(
            imei=imei,
            device_name="Test Phone",
            manufacturer="Test Manufacturer",
            model_number="TM-001",
            device_type=DeviceType.SMARTPHONE,
            customer_id=customer_id,
            sim_id=sim_id,
        )
    )


def test_create_device(db):
    service = DeviceService(db)

    device = service.create_device(
        DeviceCreate(
            imei="123456789012345",
            device_name="Test Phone",
            manufacturer="Samsung",
            model_number="SM-A001",
            device_type=DeviceType.SMARTPHONE,
        )
    )

    assert device.id is not None
    assert device.imei == "123456789012345"
    assert device.status == DeviceStatus.REGISTERED
    assert device.customer_id is None
    assert device.sim_id is None


def test_duplicate_imei_blocked(db):
    service = DeviceService(db)

    service.create_device(
        DeviceCreate(
            imei="123456789012345",
            device_name="Phone One",
            manufacturer="Samsung",
            model_number="SM-A001",
            device_type=DeviceType.SMARTPHONE,
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.create_device(
            DeviceCreate(
                imei="123456789012345",
                device_name="Phone Two",
                manufacturer="Apple",
                model_number="A001",
                device_type=DeviceType.SMARTPHONE,
            )
        )

    assert exc.value.status_code == 409
    assert "IMEI" in exc.value.detail


def test_create_device_with_customer_and_active_sim(db):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_device(
        db,
        customer_id=customer.id,
        sim_id=sim.id,
    )

    assert device.customer_id == customer.id
    assert device.sim_id == sim.id
    assert device.status == DeviceStatus.REGISTERED


def test_sim_cannot_be_assigned_to_two_devices(db):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    create_device(
        db,
        customer_id=customer.id,
        sim_id=sim.id,
        imei="123456789012345",
    )

    with pytest.raises(HTTPException) as exc:
        create_device(
            db,
            customer_id=customer.id,
            sim_id=sim.id,
            imei="123456789012346",
        )

    assert exc.value.status_code == 409


def test_activate_device_requires_active_sim(db):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = SIMCard(
        sim_number="SIM123456790",
        sim_type=SIMType.PHYSICAL,
        status=SIMStatus.AVAILABLE,
        customer_id=customer.id,
        plan_id=plan.id,
    )

    db.add(sim)
    db.commit()
    db.refresh(sim)

    device = create_device(
        db,
        customer_id=customer.id,
        sim_id=sim.id,
    )

    service = DeviceService(db)

    with pytest.raises(HTTPException) as exc:
        service.activate_device(device.id)

    assert exc.value.status_code == 400
    assert "SIM must be active" in exc.value.detail


def test_activate_device(db):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_device(
        db,
        customer_id=customer.id,
        sim_id=sim.id,
    )

    service = DeviceService(db)

    activated = service.activate_device(
        device.id
    )

    assert activated.status == DeviceStatus.ACTIVE
    assert activated.activation_date is not None


def test_only_one_active_device_per_customer(db):
    customer = create_customer(db)
    plan = create_plan(db)

    sim1 = create_active_sim(
        db,
        customer,
        plan,
        "SIM123456791",
    )

    device1 = create_device(
        db,
        customer_id=customer.id,
        sim_id=sim1.id,
        imei="123456789012345",
    )

    service = DeviceService(db)

    service.activate_device(device1.id)

    sim2 = SIMCard(
        sim_number="SIM123456792",
        sim_type=SIMType.ESIM,
        status=SIMStatus.ACTIVE,
        customer_id=customer.id,
        plan_id=plan.id,
    )

    db.add(sim2)
    db.commit()
    db.refresh(sim2)

    device2 = create_device(
        db,
        customer_id=customer.id,
        sim_id=sim2.id,
        imei="123456789012346",
    )

    with pytest.raises(HTTPException) as exc:
        service.activate_device(device2.id)

    assert exc.value.status_code == 409


def test_invalid_device_status_transition(db):
    device = create_device(db)

    service = DeviceService(db)

    device.status = DeviceStatus.DEACTIVATED
    db.commit()

    from app.schemas.device import DeviceStatusUpdate

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            device.id,
            DeviceStatusUpdate(
                status=DeviceStatus.ACTIVE
            ),
        )

    assert exc.value.status_code == 400


def test_replace_device(db):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_device(
        db,
        customer_id=customer.id,
        sim_id=sim.id,
    )

    service = DeviceService(db)

    service.activate_device(device.id)

    old_device, new_device = (
        service.replace_device(
            device.id,
            DeviceReplacementCreate(
                new_imei="987654321098765",
                device_name="Replacement Phone",
                manufacturer="Apple",
                model_number="A001",
                device_type=DeviceType.SMARTPHONE,
                reason="Device damaged",
            ),
        )
    )

    assert (
        old_device.status
        == DeviceStatus.DEACTIVATED
    )

    assert (
        new_device.status
        == DeviceStatus.REGISTERED
    )

    assert (
        new_device.customer_id
        == customer.id
    )

    assert (
        new_device.sim_id
        == sim.id
    )

    assert (
        new_device.replacement_of_device_id
        == old_device.id
    )

    assert (
        new_device.replacement_reason
        == "Device damaged"
    )