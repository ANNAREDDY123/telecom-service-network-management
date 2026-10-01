from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.subscription import (
    SubscriptionStatus,
    SubscriptionType,
)
from app.models.user import User, UserRole
from app.schemas.subscription import (
    SubscriptionCancellation,
    SubscriptionCreate,
    SubscriptionRenewal,
    SubscriptionResponse,
    SubscriptionStatusUpdate,
    SubscriptionUpdate,
)
from app.services.subscription_service import (
    SubscriptionService,
)
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
]

SUBSCRIPTION_VIEW_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
    UserRole.NETWORK_ENGINEER,
    UserRole.FIELD_TECHNICIAN,
    UserRole.CUSTOMER,
]


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subscription(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.create_subscription(data)


@router.get(
    "",
    response_model=list[SubscriptionResponse],
)
def list_subscriptions(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    subscription_type: SubscriptionType | None = None,
    subscription_status: SubscriptionStatus | None = None,
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    plan_id: int | None = Query(
        default=None,
        gt=0,
    ),
    sim_id: int | None = Query(
        default=None,
        gt=0,
    ),
    device_id: int | None = Query(
        default=None,
        gt=0,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(SUBSCRIPTION_VIEW_ROLES)
    ),
):
    service = SubscriptionService(db)

    subscriptions, _ = (
        service.search_subscriptions(
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
    )

    return subscriptions


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(SUBSCRIPTION_VIEW_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.get_subscription(
        subscription_id
    )


@router.put(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
)
def update_subscription(
    subscription_id: int,
    data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.update_subscription(
        subscription_id,
        data,
    )


@router.patch(
    "/{subscription_id}/status",
    response_model=SubscriptionResponse,
)
def update_subscription_status(
    subscription_id: int,
    data: SubscriptionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.update_status(
        subscription_id,
        data,
    )


@router.patch(
    "/{subscription_id}/activate",
    response_model=SubscriptionResponse,
)
def activate_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.activate_subscription(
        subscription_id
    )


@router.patch(
    "/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
)
def cancel_subscription(
    subscription_id: int,
    data: SubscriptionCancellation,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.cancel_subscription(
        subscription_id,
        data,
    )


@router.patch(
    "/{subscription_id}/renew",
    response_model=SubscriptionResponse,
)
def renew_subscription(
    subscription_id: int,
    data: SubscriptionRenewal,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.renew_subscription(
        subscription_id,
        data,
    )


@router.patch(
    "/{subscription_id}/expire",
    response_model=SubscriptionResponse,
)
def expire_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SubscriptionService(db)

    return service.expire_subscription(
        subscription_id
    )