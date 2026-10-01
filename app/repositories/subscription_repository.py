from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionType,
)


class SubscriptionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        subscription_id: int,
    ) -> Subscription | None:
        return self.db.scalar(
            select(Subscription).where(
                Subscription.id == subscription_id
            )
        )

    def get_by_subscription_number(
        self,
        subscription_number: str,
    ) -> Subscription | None:
        return self.db.scalar(
            select(Subscription).where(
                func.lower(
                    Subscription.subscription_number
                )
                == subscription_number.lower()
            )
        )

    def get_active_customer_subscription(
        self,
        customer_id: int,
    ) -> Subscription | None:
        return self.db.scalar(
            select(Subscription).where(
                Subscription.customer_id == customer_id,
                Subscription.status
                == SubscriptionStatus.ACTIVE,
            )
        )

    def get_active_sim_subscription(
        self,
        sim_id: int,
    ) -> Subscription | None:
        return self.db.scalar(
            select(Subscription).where(
                Subscription.sim_id == sim_id,
                Subscription.status
                == SubscriptionStatus.ACTIVE,
            )
        )

    def get_active_device_subscription(
        self,
        device_id: int,
    ) -> Subscription | None:
        return self.db.scalar(
            select(Subscription).where(
                Subscription.device_id == device_id,
                Subscription.status
                == SubscriptionStatus.ACTIVE,
            )
        )

    def create(
        self,
        subscription: Subscription,
    ) -> Subscription:
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def update(
        self,
        subscription: Subscription,
    ) -> Subscription:
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def search(
        self,
        search: str | None = None,
        subscription_type: SubscriptionType | None = None,
        subscription_status: SubscriptionStatus | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        sim_id: int | None = None,
        device_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Subscription], int]:

        query = select(Subscription)

        if search:
            pattern = f"%{search}%"

            query = query.where(
                or_(
                    Subscription.subscription_number.ilike(
                        pattern
                    ),
                )
            )

        if subscription_type is not None:
            query = query.where(
                Subscription.subscription_type
                == subscription_type
            )

        if subscription_status is not None:
            query = query.where(
                Subscription.status
                == subscription_status
            )

        if customer_id is not None:
            query = query.where(
                Subscription.customer_id
                == customer_id
            )

        if plan_id is not None:
            query = query.where(
                Subscription.plan_id == plan_id
            )

        if sim_id is not None:
            query = query.where(
                Subscription.sim_id == sim_id
            )

        if device_id is not None:
            query = query.where(
                Subscription.device_id == device_id
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(
            count_query
        ) or 0

        subscriptions = list(
            self.db.scalars(
                query
                .order_by(
                    Subscription.id.desc()
                )
                .offset(skip)
                .limit(limit)
            )
        )

        return subscriptions, total