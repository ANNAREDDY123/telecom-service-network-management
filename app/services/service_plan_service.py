from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.service_plan import (
    PlanStatus,
    ServicePlan,
)
from app.repositories.service_plan_repository import (
    ServicePlanRepository,
)
from app.schemas.service_plan import (
    ServicePlanCreate,
    ServicePlanUpdate,
)


class ServicePlanService:

    def __init__(self, db: Session):
        self.repository = ServicePlanRepository(db)

    def create_plan(
        self,
        data: ServicePlanCreate,
    ) -> ServicePlan:

        existing = self.repository.get_by_code(
            data.plan_code
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plan code already exists",
            )

        # At least one quota should be defined.
        if (
            data.data_limit_mb is None
            and data.voice_limit_minutes is None
            and data.sms_limit is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "At least one of data, voice, "
                    "or SMS limits must be provided"
                ),
            )

        plan = ServicePlan(
            plan_code=data.plan_code.strip().upper(),
            plan_name=data.plan_name.strip(),
            description=data.description,
            plan_type=data.plan_type,
            service_type=data.service_type,
            price=data.price,
            validity_days=data.validity_days,
            data_limit_mb=data.data_limit_mb,
            voice_limit_minutes=data.voice_limit_minutes,
            sms_limit=data.sms_limit,
            status=PlanStatus.ACTIVE,
        )

        return self.repository.create(plan)

    def get_plan(
        self,
        plan_id: int,
    ) -> ServicePlan:

        plan = self.repository.get_by_id(plan_id)

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service plan not found",
            )

        return plan

    def update_plan(
        self,
        plan_id: int,
        data: ServicePlanUpdate,
    ) -> ServicePlan:

        plan = self.get_plan(plan_id)

        if plan.status == PlanStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive plan cannot be updated",
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided",
            )

        for field, value in update_data.items():

            if field == "plan_name":
                value = value.strip()

            setattr(plan, field, value)

        # Prevent a plan from ending up with
        # no usable quota.
        data_limit = plan.data_limit_mb
        voice_limit = plan.voice_limit_minutes
        sms_limit = plan.sms_limit

        if (
            data_limit is None
            and voice_limit is None
            and sms_limit is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A plan must have at least one "
                    "data, voice, or SMS limit"
                ),
            )

        return self.repository.update(plan)

    def set_status(
        self,
        plan_id: int,
        status_value: PlanStatus,
    ) -> ServicePlan:

        plan = self.get_plan(plan_id)

        if plan.status == status_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Plan is already "
                    f"{status_value.value}"
                ),
            )

        plan.status = status_value

        return self.repository.update(plan)

    def search_plans(
        self,
        search: str | None = None,
        plan_type=None,
        service_type=None,
        status=None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        skip: int = 0,
        limit: int = 20,
    ):

        if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Minimum price cannot be greater "
                    "than maximum price"
                ),
            )

        return self.repository.search(
            search=search,
            plan_type=plan_type,
            service_type=service_type,
            status=status,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=limit,
        )

    def compare_plans(
        self,
        plan_ids: list[int],
    ) -> list[ServicePlan]:

        if len(plan_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least two plans are required for comparison",
            )

        if len(plan_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A maximum of five plans can be compared",
            )

        if len(set(plan_ids)) != len(plan_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate plan IDs are not allowed",
            )

        plans = []

        for plan_id in plan_ids:
            plans.append(
                self.get_plan(plan_id)
            )

        return plans