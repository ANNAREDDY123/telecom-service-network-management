from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.sla_policy import SLAPriority, SLAStatus
from app.models.sla_tracking import SLATrackingStatus
from app.schemas.sla import (
    SLABreachCheckResponse,
    SLAPolicyCreate,
    SLAPolicyListResponse,
    SLAPolicyResponse,
    SLAPolicyUpdate,
    SLAResolutionUpdate,
    SLAResponseUpdate,
    SLATrackingListResponse,
    SLATrackingResponse,
    SLAStatusUpdate,
)
from app.services.sla_service import SLAService


router = APIRouter(
    prefix="/sla",
    tags=["SLA Management"],
)


# ============================================================
# SLA POLICY ENDPOINTS
# ============================================================


@router.post(
    "/policies",
    response_model=SLAPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sla_policy(
    data: SLAPolicyCreate,
    db: Session = Depends(get_db),
):
    return SLAService.create_policy(
        db,
        data,
    )


@router.get(
    "/policies/{policy_id}",
    response_model=SLAPolicyResponse,
)
def get_sla_policy(
    policy_id: int,
    db: Session = Depends(get_db),
):
    return SLAService.get_policy(
        db,
        policy_id,
    )


@router.put(
    "/policies/{policy_id}",
    response_model=SLAPolicyResponse,
)
def update_sla_policy(
    policy_id: int,
    data: SLAPolicyUpdate,
    db: Session = Depends(get_db),
):
    return SLAService.update_policy(
        db,
        policy_id,
        data,
    )


@router.patch(
    "/policies/{policy_id}/status",
    response_model=SLAPolicyResponse,
)
def update_sla_policy_status(
    policy_id: int,
    data: SLAStatusUpdate,
    db: Session = Depends(get_db),
):
    return SLAService.update_policy_status(
        db,
        policy_id,
        data.status,
    )


@router.get(
    "/policies",
    response_model=SLAPolicyListResponse,
)
def list_sla_policies(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    priority: SLAPriority | None = None,
    status: SLAStatus | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = SLAService.list_policies(
        db=db,
        page=page,
        page_size=page_size,
        priority=priority,
        status=status,
        search=search,
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total
        else 0
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ============================================================
# SLA TRACKING ENDPOINTS
# ============================================================


@router.post(
    "/tickets/{ticket_id}/tracking",
    response_model=SLATrackingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_sla_tracking(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    from app.models.support_ticket import SupportTicket

    ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.id == ticket_id)
        .first()
    )

    if not ticket:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )

    return SLAService.create_tracking_for_ticket(
        db,
        ticket,
    )


@router.get(
    "/tracking/{tracking_id}",
    response_model=SLATrackingResponse,
)
def get_sla_tracking(
    tracking_id: int,
    db: Session = Depends(get_db),
):
    return SLAService.get_tracking(
        db,
        tracking_id,
    )


@router.get(
    "/tickets/{ticket_id}/tracking",
    response_model=SLATrackingResponse,
)
def get_ticket_sla_tracking(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    return SLAService.get_tracking_by_ticket(
        db,
        ticket_id,
    )


@router.get(
    "/tracking",
    response_model=SLATrackingListResponse,
)
def list_sla_tracking(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tracking_status: SLATrackingStatus | None = Query(
        default=None,
        alias="status",
    ),
    policy_id: int | None = None,
    ticket_id: int | None = None,
    db: Session = Depends(get_db),
):
    items, total = SLAService.list_tracking(
        db=db,
        page=page,
        page_size=page_size,
        status=tracking_status,
        policy_id=policy_id,
        ticket_id=ticket_id,
    )

    total_pages = (
        (total + page_size - 1) // page_size
        if total
        else 0
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ============================================================
# SLA RESPONSE / RESOLUTION
# ============================================================


@router.patch(
    "/tracking/{tracking_id}/response",
    response_model=SLATrackingResponse,
)
def record_sla_response(
    tracking_id: int,
    data: SLAResponseUpdate,
    db: Session = Depends(get_db),
):
    return SLAService.record_response(
        db,
        tracking_id,
        data.response_at,
    )


@router.patch(
    "/tracking/{tracking_id}/resolution",
    response_model=SLATrackingResponse,
)
def record_sla_resolution(
    tracking_id: int,
    data: SLAResolutionUpdate,
    db: Session = Depends(get_db),
):
    return SLAService.record_resolution(
        db,
        tracking_id,
        data.resolved_at,
    )


# ============================================================
# BREACH DETECTION
# ============================================================


@router.post(
    "/tracking/{tracking_id}/check-breach",
    response_model=SLABreachCheckResponse,
)
def check_sla_breach(
    tracking_id: int,
    db: Session = Depends(get_db),
):
    return SLAService.detect_breaches(
        db,
        tracking_id,
    )


@router.post(
    "/tracking/check-all-breaches",
)
def check_all_sla_breaches(
    db: Session = Depends(get_db),
):
    updated_count = SLAService.check_all_active_breaches(
        db,
    )

    return {
        "message": "SLA breach check completed",
        "updated_count": updated_count,
    }