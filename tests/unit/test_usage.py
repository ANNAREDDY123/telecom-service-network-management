from datetime import date, timedelta
from decimal import Decimal

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
from app.models.usage import (
    UsageStatus,
    UsageType,
)
from app.schemas.usage import (
    UsageCreate,
    UsageStatusUpdate,
    UsageUpdate,
)
from app.services.usage_service import (
    UsageService,
)


DATABASE_URL = "sqlite:///./test_usage.db"


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


# =========================================================
# TEST DATA HELPERS
# =========================================================


def create_customer(db):
    customer = Customer(
        user_id=1,
        customer_number="CUS001",
        full_name="Usage Customer",
        email="usage@example.com",
        phone="9876500001",
        is_active=True,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_plan(db):
    plan = ServicePlan(
        plan_code="PLAN_USAGE001",
        plan_name="Usage Test Plan",
        description="Usage tracking test plan",
        plan_type=PlanType.POSTPAID,
        service_type=ServiceType.DATA,
        price=599,
        validity_days=30,
        data_limit_mb=10000,
        voice_limit_minutes=1000,
        sms_limit=100,
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
    sim_number="SIM_USAGE001",
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
    imei="356938035643809",
):
    device = Device(
        imei=imei,
        device_name="Usage Test Phone",
        manufacturer="Samsung",
        model_number="SM-USAGE001",
        device_type=DeviceType.SMARTPHONE,
        status=DeviceStatus.ACTIVE,
        customer_id=customer.id,
        sim_id=sim.id,
        activation_date=date.today(),
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def create_active_subscription(
    db,
    customer,
    plan,
    sim,
    device,
    subscription_number="SUB_USAGE001",
):
    subscription = Subscription(
        subscription_number=subscription_number,
        subscription_type=SubscriptionType.POSTPAID,
        status=SubscriptionStatus.ACTIVE,
        customer_id=customer.id,
        plan_id=plan.id,
        sim_id=sim.id,
        device_id=device.id,
        start_date=date.today(),
        end_date=(
            date.today()
            + timedelta(
                days=plan.validity_days
            )
        ),
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


def create_usage_environment(db):
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

    subscription = create_active_subscription(
        db,
        customer,
        plan,
        sim,
        device,
    )

    return (
        customer,
        plan,
        sim,
        device,
        subscription,
    )


# =========================================================
# CREATE USAGE TESTS
# =========================================================


def test_create_data_usage(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=Decimal("500.500"),
            reference_id="DATA-001",
        )
    )

    assert usage.id is not None
    assert usage.subscription_id == subscription.id
    assert usage.customer_id == customer.id
    assert usage.usage_type == UsageType.DATA
    assert usage.data_used_mb == Decimal("500.500")
    assert usage.voice_minutes is None
    assert usage.sms_count is None
    assert usage.status == UsageStatus.RECORDED


def test_create_voice_usage(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.VOICE,
            voice_minutes=100,
            reference_id="VOICE-001",
        )
    )

    assert usage.usage_type == UsageType.VOICE
    assert usage.voice_minutes == 100
    assert usage.data_used_mb is None
    assert usage.sms_count is None


def test_create_sms_usage(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.SMS,
            sms_count=25,
            reference_id="SMS-001",
        )
    )

    assert usage.usage_type == UsageType.SMS
    assert usage.sms_count == 25
    assert usage.data_used_mb is None
    assert usage.voice_minutes is None


# =========================================================
# VALIDATION TESTS
# =========================================================


def test_usage_requires_active_subscription(db):
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

    subscription = Subscription(
        subscription_number="SUB_INACTIVE001",
        subscription_type=SubscriptionType.POSTPAID,
        status=SubscriptionStatus.SUSPENDED,
        customer_id=customer.id,
        plan_id=plan.id,
        sim_id=sim.id,
        device_id=device.id,
        start_date=date.today(),
        end_date=(
            date.today()
            + timedelta(days=30)
        ),
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    service = UsageService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer.id,
                usage_type=UsageType.DATA,
                data_used_mb=100,
            )
        )

    assert exc.value.status_code == 400
    assert (
        "active subscription"
        in exc.value.detail
    )


def test_customer_subscription_mismatch_blocked(db):
    customer1 = create_customer(db)

    customer2 = Customer(
        user_id=2,
        customer_number="CUS002",
        full_name="Second Customer",
        email="usage2@example.com",
        phone="9876500002",
        is_active=True,
    )

    db.add(customer2)
    db.commit()
    db.refresh(customer2)

    plan = create_plan(db)

    sim = create_active_sim(
        db,
        customer1,
        plan,
        "SIM_USAGE002",
    )

    device = create_active_device(
        db,
        customer1,
        sim,
        "356938035643810",
    )

    subscription = create_active_subscription(
        db,
        customer1,
        plan,
        sim,
        device,
        "SUB_USAGE002",
    )

    service = UsageService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer2.id,
                usage_type=UsageType.DATA,
                data_used_mb=100,
            )
        )

    assert exc.value.status_code == 400
    assert (
        "does not belong"
        in exc.value.detail
    )


def test_future_usage_date_blocked(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer.id,
                usage_type=UsageType.DATA,
                usage_date=(
                    date.today()
                    + timedelta(days=1)
                ),
                data_used_mb=100,
            )
        )

    assert exc.value.status_code == 400
    assert "future" in exc.value.detail


def test_usage_type_measurement_mismatch_blocked(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer.id,
                usage_type=UsageType.DATA,
                data_used_mb=100,
                voice_minutes=10,
            )
        )

    assert exc.value.status_code == 400
    assert (
        "voice minutes"
        in exc.value.detail
    )


def test_duplicate_reference_id_blocked(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=100,
            reference_id="DUPLICATE-001",
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer.id,
                usage_type=UsageType.DATA,
                data_used_mb=200,
                reference_id="DUPLICATE-001",
            )
        )

    assert exc.value.status_code == 409
    assert (
        "reference ID"
        in exc.value.detail
    )


# =========================================================
# PLAN ALLOWANCE TESTS
# =========================================================


def test_data_plan_limit_enforced(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=9000,
            reference_id="DATA-LIMIT-001",
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer.id,
                usage_type=UsageType.DATA,
                data_used_mb=1500,
                reference_id="DATA-LIMIT-002",
            )
        )

    assert exc.value.status_code == 409
    assert "plan limit" in exc.value.detail


def test_voice_plan_limit_enforced(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.VOICE,
            voice_minutes=900,
            reference_id="VOICE-LIMIT-001",
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer.id,
                usage_type=UsageType.VOICE,
                voice_minutes=200,
                reference_id="VOICE-LIMIT-002",
            )
        )

    assert exc.value.status_code == 409
    assert "plan limit" in exc.value.detail


def test_sms_plan_limit_enforced(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.SMS,
            sms_count=90,
            reference_id="SMS-LIMIT-001",
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.create_usage(
            UsageCreate(
                subscription_id=subscription.id,
                customer_id=customer.id,
                usage_type=UsageType.SMS,
                sms_count=20,
                reference_id="SMS-LIMIT-002",
            )
        )

    assert exc.value.status_code == 409
    assert "plan limit" in exc.value.detail


# =========================================================
# UPDATE TESTS
# =========================================================


def test_update_recorded_usage(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=100,
            reference_id="UPDATE-001",
        )
    )

    updated = service.update_usage(
        usage.id,
        UsageUpdate(
            data_used_mb=250,
            remarks="Updated usage",
        ),
    )

    assert updated.data_used_mb == Decimal("250")
    assert updated.remarks == "Updated usage"


def test_processed_usage_cannot_be_updated(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=100,
            reference_id="PROCESSED-001",
        )
    )

    service.process_usage(usage.id)

    with pytest.raises(HTTPException) as exc:
        service.update_usage(
            usage.id,
            UsageUpdate(
                data_used_mb=200
            ),
        )

    assert exc.value.status_code == 400
    assert (
        "Recorded usage"
        in exc.value.detail
    )


# =========================================================
# STATUS LIFECYCLE TESTS
# =========================================================


def test_process_usage(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=100,
            reference_id="PROCESS-001",
        )
    )

    processed = service.process_usage(
        usage.id
    )

    assert (
        processed.status
        == UsageStatus.PROCESSED
    )


def test_reverse_usage(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=100,
            reference_id="REVERSE-001",
        )
    )

    reversed_usage = service.reverse_usage(
        usage.id,
        "Incorrect network record",
    )

    assert (
        reversed_usage.status
        == UsageStatus.REVERSED
    )

    assert (
        "Incorrect network record"
        in reversed_usage.remarks
    )


def test_invalid_usage_status_transition(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    usage = service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=100,
            reference_id="STATUS-001",
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.update_status(
            usage.id,
            UsageStatusUpdate(
                status=UsageStatus.RECORDED
            ),
        )

    assert exc.value.status_code == 400
    assert (
        "Invalid usage status transition"
        in exc.value.detail
    )


# =========================================================
# SUMMARY TEST
# =========================================================


def test_usage_summary(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=500,
            reference_id="SUMMARY-DATA-001",
        )
    )

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.VOICE,
            voice_minutes=100,
            reference_id="SUMMARY-VOICE-001",
        )
    )

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.SMS,
            sms_count=10,
            reference_id="SUMMARY-SMS-001",
        )
    )

    summary = service.get_usage_summary(
        subscription.id
    )

    assert (
        summary.customer_id
        == customer.id
    )

    assert (
        summary.subscription_id
        == subscription.id
    )

    assert (
        summary.total_data_used_mb
        == Decimal("500")
    )

    assert (
        summary.total_voice_minutes
        == 100
    )

    assert (
        summary.total_sms_count
        == 10
    )

    assert summary.data_limit_mb == 10000

    assert (
        summary.voice_limit_minutes
        == 1000
    )

    assert summary.sms_limit == 100

    assert (
        summary.remaining_data_mb
        == Decimal("9500")
    )

    assert (
        summary.remaining_voice_minutes
        == 900
    )

    assert summary.remaining_sms == 90


# =========================================================
# SEARCH TESTS
# =========================================================


def test_search_usage(db):
    (
        customer,
        plan,
        sim,
        device,
        subscription,
    ) = create_usage_environment(db)

    service = UsageService(db)

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.DATA,
            data_used_mb=100,
            reference_id="SEARCH-DATA-001",
        )
    )

    service.create_usage(
        UsageCreate(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=UsageType.SMS,
            sms_count=5,
            reference_id="SEARCH-SMS-001",
        )
    )

    result = service.search_usage(
        subscription_id=subscription.id,
        usage_type=UsageType.DATA,
        skip=0,
        limit=20,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1

    assert (
        result["items"][0].usage_type
        == UsageType.DATA
    )


def test_invalid_search_date_range(db):
    create_usage_environment(db)

    service = UsageService(db)

    with pytest.raises(HTTPException) as exc:
        service.search_usage(
            start_date=date.today(),
            end_date=(
                date.today()
                - timedelta(days=1)
            ),
        )

    assert exc.value.status_code == 400
    assert "Start date" in exc.value.detail