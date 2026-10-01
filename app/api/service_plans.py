from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.service_plan import (
    PlanStatus,
    PlanType,
    ServiceType,
)
from app.models.user import User, UserRole
from app.schemas.service_plan import (
    ServicePlanComparisonResponse,
    ServicePlanCreate,
    ServicePlanResponse,
    ServicePlanStatusResponse,
    ServicePlanUpdate,
)
from app.services.service_plan_service import (
    ServicePlanService,
)
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/service-plans",
    tags=["Telecom Service Plans"],
)


MANAGEMENT_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
)


@router.post(
    "",
    response_model=ServicePlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(
    data: ServicePlanCreate,
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = ServicePlanService(db)

    return service.create_plan(data)


@router.get(
    "",
)
def list_plans(
    search: str | None = Query(
        default=None
    ),
    plan_type: PlanType | None = Query(
        default=None
    ),
    service_type: ServiceType | None = Query(
        default=None
    ),
    plan_status: PlanStatus | None = Query(
        default=None
    ),
    min_price: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    max_price: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.CUSTOMER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ServicePlanService(db)

    skip = (page - 1) * page_size

    plans, total = service.search_plans(
        search=search,
        plan_type=plan_type,
        service_type=service_type,
        status=plan_status,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=page_size,
    )

    return {
        "items": plans,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (
            (total + page_size - 1)
            // page_size
            if total
            else 0
        ),
    }


@router.get(
    "/compare",
    response_model=ServicePlanComparisonResponse,
)
def compare_plans(
    plan_ids: list[int] = Query(
        min_length=2,
        max_length=5,
    ),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.CUSTOMER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ServicePlanService(db)

    plans = service.compare_plans(plan_ids)

    return {
        "plans": plans
    }


@router.get(
    "/{plan_id}",
    response_model=ServicePlanResponse,
)
def get_plan(
    plan_id: int,
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.CUSTOMER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = ServicePlanService(db)

    return service.get_plan(plan_id)


@router.put(
    "/{plan_id}",
    response_model=ServicePlanResponse,
)
def update_plan(
    plan_id: int,
    data: ServicePlanUpdate,
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = ServicePlanService(db)

    return service.update_plan(
        plan_id,
        data,
    )


@router.patch(
    "/{plan_id}/activate",
    response_model=ServicePlanStatusResponse,
)
def activate_plan(
    plan_id: int,
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = ServicePlanService(db)

    plan = service.set_status(
        plan_id,
        PlanStatus.ACTIVE,
    )

    return {
        "message": "Service plan activated successfully",
        "plan": plan,
    }


@router.patch(
    "/{plan_id}/deactivate",
    response_model=ServicePlanStatusResponse,
)
def deactivate_plan(
    plan_id: int,
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = ServicePlanService(db)

    plan = service.set_status(
        plan_id,
        PlanStatus.INACTIVE,
    )

    return {
        "message": "Service plan deactivated successfully",
        "plan": plan,
    }