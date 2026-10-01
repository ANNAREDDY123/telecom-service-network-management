from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.network_outage import (
    OutageSeverity,
    OutageStatus,
    OutageType,
)
from app.schemas.network_outage import (
    AffectedCustomerListResponse,
    AffectedCustomerResponse,
    AffectedCustomersCreate,
    OutageCreate,
    OutageListResponse,
    OutageResponse,
    OutageRestore,
    OutageStatusUpdate,
    OutageSummaryResponse,
    OutageUpdate,
)
from app.services.network_outage_service import (
    NetworkOutageService,
)
from app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/network-outages",
    tags=["Network Outages"],
)


@router.post(
    "",
    response_model=OutageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_outage(
    data: OutageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.create_outage(
        data,
        created_by=current_user.id,
    )


@router.get(
    "",
    response_model=OutageListResponse,
)
def list_outages(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        10,
        ge=1,
        le=100,
    ),
    outage_status: OutageStatus | None = Query(
        default=None,
        alias="status",
    ),
    severity: OutageSeverity | None = None,
    outage_type: OutageType | None = None,
    tower_id: int | None = Query(
        default=None,
        gt=0,
    ),
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    items, total = service.list_outages(
        page=page,
        page_size=page_size,
        status=outage_status,
        severity=severity,
        outage_type=outage_type,
        tower_id=tower_id,
        search=search,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/active",
    response_model=list[OutageResponse],
)
def get_active_outages(
    tower_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.get_active_outages(
        tower_id=tower_id
    )


@router.get(
    "/{outage_id}",
    response_model=OutageResponse,
)
def get_outage(
    outage_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.get_outage(
        outage_id
    )


@router.put(
    "/{outage_id}",
    response_model=OutageResponse,
)
def update_outage(
    outage_id: int,
    data: OutageUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.update_outage(
        outage_id,
        data,
    )


@router.patch(
    "/{outage_id}/status",
    response_model=OutageResponse,
)
def update_outage_status(
    outage_id: int,
    data: OutageStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.update_status(
        outage_id,
        data,
    )


@router.post(
    "/{outage_id}/restore",
    response_model=OutageResponse,
)
def restore_outage(
    outage_id: int,
    data: OutageRestore,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.restore_outage(
        outage_id,
        data,
    )


@router.post(
    "/{outage_id}/close",
    response_model=OutageResponse,
)
def close_outage(
    outage_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.close_outage(
        outage_id
    )


@router.post(
    "/{outage_id}/cancel",
    response_model=OutageResponse,
)
def cancel_outage(
    outage_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.cancel_outage(
        outage_id
    )


@router.post(
    "/{outage_id}/affected-customers",
    response_model=list[AffectedCustomerResponse],
    status_code=status.HTTP_201_CREATED,
)
def identify_affected_customers(
    outage_id: int,
    data: AffectedCustomersCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.identify_affected_customers(
        outage_id,
        data,
    )


@router.get(
    "/{outage_id}/affected-customers",
    response_model=AffectedCustomerListResponse,
)
def get_affected_customers(
    outage_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    items = service.get_affected_customers(
        outage_id
    )

    return {
        "items": items,
        "total": len(items),
    }


@router.get(
    "/{outage_id}/summary",
    response_model=OutageSummaryResponse,
)
def get_outage_summary(
    outage_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NetworkOutageService(db)

    return service.get_outage_summary(
        outage_id
    )