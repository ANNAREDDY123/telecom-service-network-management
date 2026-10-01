from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.device import Device, DeviceStatus
from app.models.service_plan import PlanStatus, ServicePlan
from app.models.sim_card import SIMCard, SIMStatus
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
)
from app.repositories.subscription_repository import (
    SubscriptionRepository,
)
from app.schemas.subscription import (
    SubscriptionCancellation,
    SubscriptionCreate,
    SubscriptionRenewal,
    SubscriptionStatusUpdate,
    SubscriptionUpdate,
)


class SubscriptionService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = SubscriptionRepository(db)

    def get_subscription(
        self,
        subscription_id: int,
    ) -> Subscription:

        subscription = self.repository.get_by_id(
            subscription_id
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        return subscription

    def validate_customer(
        self,
        customer_id: int,
    ) -> Customer:

        customer = self.db.get(
            Customer,
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer account is inactive",
            )

        return customer

    def validate_plan(
        self,
        plan_id: int,
    ) -> ServicePlan:

        plan = self.db.get(
            ServicePlan,
            plan_id,
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service plan not found",
            )

        if plan.status != PlanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service plan is inactive",
            )

        return plan

    def validate_sim(
        self,
        sim_id: int,
        customer_id: int,
    ) -> SIMCard:

        sim = self.db.get(
            SIMCard,
            sim_id,
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM card not found",
            )

        if sim.status != SIMStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SIM card must be active",
            )

        if sim.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIM card is assigned to a different customer"
                ),
            )

        return sim

    def validate_device(
        self,
        device_id: int,
        customer_id: int,
        sim_id: int,
    ) -> Device:

        device = self.db.get(
            Device,
            device_id,
        )

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        if device.status != DeviceStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device must be active",
            )

        if device.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Device is assigned to a different customer"
                ),
            )

        if device.sim_id != sim_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Device is not assigned to the specified SIM"
                ),
            )

        return device

    def create_subscription(
        self,
        data: SubscriptionCreate,
    ) -> Subscription:

        existing = (
            self.repository.get_by_subscription_number(
                data.subscription_number
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Subscription number already exists",
            )

        self.validate_customer(
            data.customer_id
        )

        self.validate_plan(
            data.plan_id
        )

        self.validate_sim(
            data.sim_id,
            data.customer_id,
        )

        self.validate_device(
            data.device_id,
            data.customer_id,
            data.sim_id,
        )

        subscription = Subscription(
            subscription_number=(
                data.subscription_number.strip()
            ),
            subscription_type=data.subscription_type,
            status=SubscriptionStatus.PENDING,
            customer_id=data.customer_id,
            plan_id=data.plan_id,
            sim_id=data.sim_id,
            device_id=data.device_id,
        )

        return self.repository.create(
            subscription
        )

    def update_subscription(
        self,
        subscription_id: int,
        data: SubscriptionUpdate,
    ) -> Subscription:

        subscription = self.get_subscription(
            subscription_id
        )

        if subscription.status in {
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Cancelled or expired subscription "
                    "cannot be updated"
                ),
            )

        new_plan_id = (
            data.plan_id
            if data.plan_id is not None
            else subscription.plan_id
        )

        new_sim_id = (
            data.sim_id
            if data.sim_id is not None
            else subscription.sim_id
        )

        new_device_id = (
            data.device_id
            if data.device_id is not None
            else subscription.device_id
        )

        self.validate_plan(
            new_plan_id
        )

        self.validate_sim(
            new_sim_id,
            subscription.customer_id,
        )

        self.validate_device(
            new_device_id,
            subscription.customer_id,
            new_sim_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(
                subscription,
                field,
                value,
            )

        return self.repository.update(
            subscription
        )

    def activate_subscription(
        self,
        subscription_id: int,
    ) -> Subscription:

        subscription = self.get_subscription(
            subscription_id
        )

        if subscription.status == SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already active",
            )

        if subscription.status not in {
            SubscriptionStatus.PENDING,
            SubscriptionStatus.SUSPENDED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Pending or Suspended "
                    "subscriptions can be activated"
                ),
            )

        self.validate_customer(
            subscription.customer_id
        )

        self.validate_plan(
            subscription.plan_id
        )

        self.validate_sim(
            subscription.sim_id,
            subscription.customer_id,
        )

        self.validate_device(
            subscription.device_id,
            subscription.customer_id,
            subscription.sim_id,
        )

        existing_customer = (
            self.repository.get_active_customer_subscription(
                subscription.customer_id
            )
        )

        if (
            existing_customer
            and existing_customer.id != subscription.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Customer already has an active subscription"
                ),
            )

        existing_sim = (
            self.repository.get_active_sim_subscription(
                subscription.sim_id
            )
        )

        if (
            existing_sim
            and existing_sim.id != subscription.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "SIM already has an active subscription"
                ),
            )

        existing_device = (
            self.repository.get_active_device_subscription(
                subscription.device_id
            )
        )

        if (
            existing_device
            and existing_device.id != subscription.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Device already has an active subscription"
                ),
            )

        plan = self.validate_plan(
            subscription.plan_id
        )

        today = date.today()

        subscription.status = (
            SubscriptionStatus.ACTIVE
        )

        subscription.start_date = today

        subscription.end_date = (
            today
            + timedelta(
                days=plan.validity_days
            )
        )

        return self.repository.update(
            subscription
        )

    def update_status(
        self,
        subscription_id: int,
        data: SubscriptionStatusUpdate,
    ) -> Subscription:

        subscription = self.get_subscription(
            subscription_id
        )

        new_status = data.status

        if subscription.status == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Subscription is already "
                    f"{new_status.value}"
                ),
            )

        allowed_transitions = {
            SubscriptionStatus.PENDING: {
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.CANCELLED,
            },
            SubscriptionStatus.ACTIVE: {
                SubscriptionStatus.SUSPENDED,
                SubscriptionStatus.EXPIRED,
                SubscriptionStatus.CANCELLED,
            },
            SubscriptionStatus.SUSPENDED: {
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.CANCELLED,
            },
            SubscriptionStatus.EXPIRED: set(),
            SubscriptionStatus.CANCELLED: set(),
        }

        if new_status not in allowed_transitions.get(
            subscription.status,
            set(),
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid subscription status "
                    "transition: "
                    f"{subscription.status.value} -> "
                    f"{new_status.value}"
                ),
            )

        if new_status == SubscriptionStatus.ACTIVE:
            return self.activate_subscription(
                subscription_id
            )

        if new_status == SubscriptionStatus.EXPIRED:
            subscription.end_date = date.today()

        if new_status == SubscriptionStatus.CANCELLED:
            subscription.cancellation_date = date.today()

        subscription.status = new_status

        return self.repository.update(
            subscription
        )

    def cancel_subscription(
        self,
        subscription_id: int,
        data: SubscriptionCancellation,
    ) -> Subscription:

        subscription = self.get_subscription(
            subscription_id
        )

        if subscription.status in {
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Subscription is already closed"
                ),
            )

        subscription.status = (
            SubscriptionStatus.CANCELLED
        )

        subscription.cancellation_date = date.today()

        subscription.cancellation_reason = (
            data.reason.strip()
        )

        return self.repository.update(
            subscription
        )

    def renew_subscription(
        self,
        subscription_id: int,
        data: SubscriptionRenewal,
    ) -> Subscription:

        subscription = self.get_subscription(
            subscription_id
        )

        if subscription.status not in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.EXPIRED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Active or Expired "
                    "subscriptions can be renewed"
                ),
            )

        plan_id = (
            data.plan_id
            if data.plan_id is not None
            else subscription.plan_id
        )

        plan = self.validate_plan(
            plan_id
        )

        subscription.plan_id = plan_id

        today = date.today()

        if (
            subscription.end_date is not None
            and subscription.end_date >= today
        ):
            start_date = subscription.end_date
        else:
            start_date = today

        subscription.start_date = (
            subscription.start_date
            or today
        )

        subscription.end_date = (
            start_date
            + timedelta(
                days=plan.validity_days
            )
        )

        subscription.status = (
            SubscriptionStatus.ACTIVE
        )

        subscription.renewal_count += 1

        subscription.cancellation_date = None
        subscription.cancellation_reason = None

        return self.repository.update(
            subscription
        )

    def expire_subscription(
        self,
        subscription_id: int,
    ) -> Subscription:

        subscription = self.get_subscription(
            subscription_id
        )

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only active subscriptions "
                    "can be expired"
                ),
            )

        if (
            subscription.end_date is not None
            and subscription.end_date > date.today()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Subscription has not reached "
                    "its expiry date"
                ),
            )

        subscription.status = (
            SubscriptionStatus.EXPIRED
        )

        return self.repository.update(
            subscription
        )

    def search_subscriptions(
        self,
        search: str | None = None,
        subscription_type=None,
        subscription_status=None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        sim_id: int | None = None,
        device_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ):

        return self.repository.search(
            search=search,
            subscription_type=subscription_type,
            subscription_status=subscription_status,
            customer_id=customer_id,
            plan_id=plan_id,
            sim_id=sim_id,
            device_id=device_id,
            skip=skip,
            limit=limit,
        )