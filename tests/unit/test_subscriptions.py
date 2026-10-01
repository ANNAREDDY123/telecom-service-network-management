from datetime import date, timedelta

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
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionType,
)
from app.schemas.subscription import (
    SubscriptionCancellation,
    SubscriptionCreate,
    SubscriptionRenewal,
)
from app.services.subscription_service import (
    SubscriptionService,
)


DATABASE_URL = "sqlite:///./test_subscriptions.db"


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
        full_name="Subscription Customer",
        email="subscription@example.com",
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
        plan_name="Subscription Plan",
        description="Test subscription plan",
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
        activation_date=date.today(),
        customer_id=customer.id,
        plan_id=plan.id,
    )

    db.add(sim)
    db.commit()
    db.refresh(sim)

    return sim


def create_active_device(
    db,
    customer,
    sim,
    imei="123456789012345",
):
    device = Device(
        imei=imei,
        device_name="Test Phone",
        manufacturer="Samsung",
        model_number="SM-001",
        device_type=DeviceType.SMARTPHONE,
        status=DeviceStatus.ACTIVE,
        customer_id=customer.id,
        sim_id=sim.id,
        activation_date=None,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def create_subscription(
    db,
    customer,
    plan,
    sim,
    device,
    subscription_number="SUB001",
):
    service = SubscriptionService(db)

    return service.create_subscription(
        SubscriptionCreate(
            subscription_number=subscription_number,
            subscription_type=SubscriptionType.POSTPAID,
            customer_id=customer.id,
            plan_id=plan.id,
            sim_id=sim.id,
            device_id=device.id,
        )
    )


def test_create_pending_subscription(db):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_active_device(
        db,
        customer,
        sim,
    )

    subscription = create_subscription(
        db,
        customer,
        plan,
        sim,
        device,
    )

    assert subscription.id is not None

    assert (
        subscription.subscription_number
        == "SUB001"
    )

    assert (
        subscription.status
        == SubscriptionStatus.PENDING
    )

    assert subscription.customer_id == customer.id
    assert subscription.plan_id == plan.id
    assert subscription.sim_id == sim.id
    assert subscription.device_id == device.id


def test_duplicate_subscription_number_blocked(
    db,
):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_active_device(
        db,
        customer,
        sim,
    )

    create_subscription(
        db,
        customer,
        plan,
        sim,
        device,
    )

    with pytest.raises(HTTPException) as exc:
        create_subscription(
            db,
            customer,
            plan,
            sim,
            device,
            subscription_number="SUB001",
        )

    assert exc.value.status_code == 409


def test_subscription_activation(
    db,
):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_active_device(
        db,
        customer,
        sim,
    )

    subscription = create_subscription(
        db,
        customer,
        plan,
        sim,
        device,
    )

    service = SubscriptionService(db)

    activated = service.activate_subscription(
        subscription.id
    )

    assert (
        activated.status
        == SubscriptionStatus.ACTIVE
    )

    assert activated.start_date == date.today()

    assert (
        activated.end_date
        == date.today()
        + timedelta(days=plan.validity_days)
    )


def test_activation_requires_active_sim(
    db,
):
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

    device = create_active_device(
        db,
        customer,
        sim,
    )

    # Create the subscription directly in PENDING state.
    # The service create_subscription() correctly requires
    # an active SIM, so this test must bypass creation
    # validation to test activation validation.
    subscription = Subscription(
        subscription_number="SUB002",
        subscription_type=SubscriptionType.POSTPAID,
        status=SubscriptionStatus.PENDING,
        customer_id=customer.id,
        plan_id=plan.id,
        sim_id=sim.id,
        device_id=device.id,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    service = SubscriptionService(db)

    with pytest.raises(HTTPException) as exc:
        service.activate_subscription(
            subscription.id
        )

    assert exc.value.status_code == 400
    assert "SIM card must be active" in exc.value.detail


def test_activation_requires_active_device(
    db,
):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
        "SIM123456793",
    )

    device = Device(
        imei="123456789012346",
        device_name="Inactive Phone",
        manufacturer="Samsung",
        model_number="SM-002",
        device_type=DeviceType.SMARTPHONE,
        status=DeviceStatus.REGISTERED,
        customer_id=customer.id,
        sim_id=sim.id,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    # Create the subscription directly in PENDING state.
    # The service create_subscription() correctly requires
    # an active device, so this test must bypass creation
    # validation to test activation validation.
    subscription = Subscription(
        subscription_number="SUB003",
        subscription_type=SubscriptionType.POSTPAID,
        status=SubscriptionStatus.PENDING,
        customer_id=customer.id,
        plan_id=plan.id,
        sim_id=sim.id,
        device_id=device.id,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    service = SubscriptionService(db)

    with pytest.raises(HTTPException) as exc:
        service.activate_subscription(
            subscription.id
        )

    assert exc.value.status_code == 400
    assert "Device must be active" in exc.value.detail


def test_only_one_active_subscription_per_customer(
    db,
):
    customer = create_customer(db)
    plan = create_plan(db)

    sim1 = create_active_sim(
        db,
        customer,
        plan,
        "SIM123456791",
    )

    device1 = create_active_device(
        db,
        customer,
        sim1,
        "123456789012346",
    )

    subscription1 = create_subscription(
        db,
        customer,
        plan,
        sim1,
        device1,
        "SUB001",
    )

    service = SubscriptionService(db)

    service.activate_subscription(
        subscription1.id
    )

    sim2 = create_active_sim(
        db,
        customer,
        plan,
        "SIM123456792",
    )

    device2 = create_active_device(
        db,
        customer,
        sim2,
        "123456789012347",
    )

    subscription2 = create_subscription(
        db,
        customer,
        plan,
        sim2,
        device2,
        "SUB002",
    )

    with pytest.raises(HTTPException) as exc:
        service.activate_subscription(
            subscription2.id
        )

    assert exc.value.status_code == 409
    assert "active subscription" in exc.value.detail


def test_cancel_subscription(
    db,
):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_active_device(
        db,
        customer,
        sim,
    )

    subscription = create_subscription(
        db,
        customer,
        plan,
        sim,
        device,
    )

    service = SubscriptionService(db)

    service.activate_subscription(
        subscription.id
    )

    cancelled = service.cancel_subscription(
        subscription.id,
        SubscriptionCancellation(
            reason="Customer requested cancellation"
        ),
    )

    assert (
        cancelled.status
        == SubscriptionStatus.CANCELLED
    )

    assert (
        cancelled.cancellation_date
        == date.today()
    )

    assert (
        cancelled.cancellation_reason
        == "Customer requested cancellation"
    )


def test_renew_subscription(
    db,
):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_active_device(
        db,
        customer,
        sim,
    )

    subscription = create_subscription(
        db,
        customer,
        plan,
        sim,
        device,
    )

    service = SubscriptionService(db)

    service.activate_subscription(
        subscription.id
    )

    original_end_date = subscription.end_date

    renewed = service.renew_subscription(
        subscription.id,
        SubscriptionRenewal(),
    )

    assert (
        renewed.status
        == SubscriptionStatus.ACTIVE
    )

    assert (
        renewed.renewal_count == 1
    )

    assert (
        renewed.end_date
        == original_end_date
        + timedelta(days=plan.validity_days)
    )


def test_invalid_status_transition(
    db,
):
    customer = create_customer(db)
    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer,
        plan,
    )

    device = create_active_device(
        db,
        customer,
        sim,
    )

    subscription = create_subscription(
        db,
        customer,
        plan,
        sim,
        device,
    )

    from app.schemas.subscription import (
        SubscriptionStatusUpdate,
    )

    service = SubscriptionService(db)

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            subscription.id,
            SubscriptionStatusUpdate(
                status=SubscriptionStatus.EXPIRED
            ),
        )

    assert exc.value.status_code == 400