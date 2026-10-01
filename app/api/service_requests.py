from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.utils.dependencies import get_current_user
from app.db.database import get_db
from app.models.service_request import (
    ServiceRequestPriority,
    ServiceRequestStatus,
    ServiceRequestType,
)
from app.models.user import User
from app.schemas.service_request import (
    ServiceRequestCompletion,
    ServiceRequestCreate,
    ServiceRequestRejection,
    ServiceRequestResponse,
    ServiceRequestStatusUpdate,
    ServiceRequestUpdate,
)
from app.services.service_request_service import (
    ServiceRequestService,
)


router = APIRouter(
    prefix="/service-requests",
    tags=["Service Requests"],
)


@router.post(
    "",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service_request(
    data: ServiceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.create(
        db,
        data,
    )


@router.get(
    "/{request_id}",
    response_model=ServiceRequestResponse,
)
def get_service_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.get(
        db,
        request_id,
    )


@router.get(
    "",
)
def list_service_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = None,
    request_type: ServiceRequestType | None = None,
    priority: ServiceRequestPriority | None = None,
    status_filter: ServiceRequestStatus | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.list_response(
        db,
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        request_type=request_type,
        priority=priority,
        status_filter=status_filter,
        search=search,
    )


@router.patch(
    "/{request_id}",
    response_model=ServiceRequestResponse,
)
def update_service_request(
    request_id: int,
    data: ServiceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.update(
        db,
        request_id,
        data,
    )


@router.patch(
    "/{request_id}/status",
    response_model=ServiceRequestResponse,
)
def update_service_request_status(
    request_id: int,
    data: ServiceRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.update_status(
        db,
        request_id,
        data,
        current_user,
    )


@router.post(
    "/{request_id}/approve",
    response_model=ServiceRequestResponse,
)
def approve_service_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.approve(
        db,
        request_id,
        current_user,
    )


@router.post(
    "/{request_id}/reject",
    response_model=ServiceRequestResponse,
)
def reject_service_request(
    request_id: int,
    data: ServiceRequestRejection,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.reject(
        db,
        request_id,
        data,
        current_user,
    )


@router.post(
    "/{request_id}/complete",
    response_model=ServiceRequestResponse,
)
def complete_service_request(
    request_id: int,
    data: ServiceRequestCompletion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.complete(
        db,
        request_id,
        data,
        current_user,
    )


@router.post(
    "/{request_id}/cancel",
    response_model=ServiceRequestResponse,
)
def cancel_service_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ServiceRequestService.cancel(
        db,
        request_id,
        current_user,
    )