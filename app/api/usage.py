from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usage import (
    UsageSource,
    UsageStatus,
    UsageType,
)
from app.schemas.usage import (
    UsageCreate,
    UsageResponse,
    UsageStatusUpdate,
    UsageSummaryResponse,
    UsageUpdate,
)
from app.services.usage_service import UsageService
from app.utils.dependencies import (
    get_current_user,
    require_roles,
)
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/usage",
    tags=["Usage Tracking"],
)


# ---------------------------------------------------------
# Create Usage
# ---------------------------------------------------------

@router.post(
    "",
    response_model=UsageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_usage(
    payload: UsageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = UsageService(db)

    return service.create_usage(payload)


# ---------------------------------------------------------
# Get Usage
# ---------------------------------------------------------

@router.get(
    "/{usage_id}",
    response_model=UsageResponse,
)
def get_usage(
    usage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = UsageService(db)

    return service.get_usage(
        usage_id
    )


# ---------------------------------------------------------
# Update Usage
# ---------------------------------------------------------

@router.put(
    "/{usage_id}",
    response_model=UsageResponse,
)
def update_usage(
    usage_id: int,
    payload: UsageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = UsageService(db)

    return service.update_usage(
        usage_id,
        payload,
    )


# ---------------------------------------------------------
# Search / Filter Usage
# ---------------------------------------------------------

@router.get(
    "",
)
def search_usage(
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    subscription_id: int | None = Query(
        default=None,
        gt=0,
    ),
    usage_type: UsageType | None = None,
    usage_status: UsageStatus | None = Query(
        default=None,
        alias="status",
    ),
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = Query(
        default=None,
        max_length=100,
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
        get_current_user
    ),
):
    service = UsageService(db)

    return service.search_usage(
        customer_id=customer_id,
        subscription_id=subscription_id,
        usage_type=usage_type,
        status=usage_status,
        start_date=start_date,
        end_date=end_date,
        search=search,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------
# Update Usage Status
# ---------------------------------------------------------

@router.patch(
    "/{usage_id}/status",
    response_model=UsageResponse,
)
def update_usage_status(
    usage_id: int,
    payload: UsageStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = UsageService(db)

    return service.update_status(
        usage_id,
        payload,
    )


# ---------------------------------------------------------
# Process Usage
# ---------------------------------------------------------

@router.patch(
    "/{usage_id}/process",
    response_model=UsageResponse,
)
def process_usage(
    usage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = UsageService(db)

    return service.process_usage(
        usage_id
    )


# ---------------------------------------------------------
# Reverse Usage
# ---------------------------------------------------------

@router.patch(
    "/{usage_id}/reverse",
    response_model=UsageResponse,
)
def reverse_usage(
    usage_id: int,
    reason: str | None = Query(
        default=None,
        max_length=500,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = UsageService(db)

    return service.reverse_usage(
        usage_id,
        reason,
    )


# ---------------------------------------------------------
# Usage Summary
# ---------------------------------------------------------

@router.get(
    "/subscription/{subscription_id}/summary",
    response_model=UsageSummaryResponse,
)
def get_usage_summary(
    subscription_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = UsageService(db)

    return service.get_usage_summary(
        subscription_id=subscription_id,
        start_date=start_date,
        end_date=end_date,
    )