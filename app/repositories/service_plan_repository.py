from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.service_plan import (
    PlanStatus,
    PlanType,
    ServicePlan,
    ServiceType,
)


class ServicePlanRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        plan_id: int,
    ) -> ServicePlan | None:

        return self.db.scalar(
            select(ServicePlan).where(
                ServicePlan.id == plan_id
            )
        )

    def get_by_code(
        self,
        plan_code: str,
    ) -> ServicePlan | None:

        return self.db.scalar(
            select(ServicePlan).where(
                func.lower(ServicePlan.plan_code)
                == plan_code.lower()
            )
        )

    def create(
        self,
        plan: ServicePlan,
    ) -> ServicePlan:

        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)

        return plan

    def update(
        self,
        plan: ServicePlan,
    ) -> ServicePlan:

        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)

        return plan

    def search(
        self,
        search: str | None = None,
        plan_type: PlanType | None = None,
        service_type: ServiceType | None = None,
        status: PlanStatus | None = None,
        min_price=None,
        max_price=None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[ServicePlan], int]:

        query = select(ServicePlan)

        if search:
            pattern = f"%{search}%"

            query = query.where(
                or_(
                    ServicePlan.plan_code.ilike(
                        pattern
                    ),
                    ServicePlan.plan_name.ilike(
                        pattern
                    ),
                    ServicePlan.description.ilike(
                        pattern
                    ),
                )
            )

        if plan_type is not None:
            query = query.where(
                ServicePlan.plan_type == plan_type
            )

        if service_type is not None:
            query = query.where(
                ServicePlan.service_type
                == service_type
            )

        if status is not None:
            query = query.where(
                ServicePlan.status == status
            )

        if min_price is not None:
            query = query.where(
                ServicePlan.price >= min_price
            )

        if max_price is not None:
            query = query.where(
                ServicePlan.price <= max_price
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        plans = list(
            self.db.scalars(
                query
                .order_by(ServicePlan.id.desc())
                .offset(skip)
                .limit(limit)
            )
        )

        return plans, total