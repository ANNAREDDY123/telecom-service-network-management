from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.models.support_ticket import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketListResponse,
    SupportTicketResponse,
    SupportTicketUpdate,
    TicketResolution,
    TicketStatusUpdate,
)
from app.services.support_ticket_service import SupportTicketService
from app.utils.dependencies import (
    get_current_user,
    get_db,
    require_roles,
)
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/support-tickets",
    tags=["Support Tickets"],
)

service = SupportTicketService()


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
    UserRole.NETWORK_ENGINEER,
    UserRole.FIELD_TECHNICIAN,
]


@router.post(
    "/",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    data: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [
                UserRole.SUPER_ADMIN,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SUPPORT_AGENT,
                UserRole.NETWORK_ENGINEER,
                UserRole.FIELD_TECHNICIAN,
                UserRole.CUSTOMER,
            ]
        )
    ),
):
    return service.create_ticket(db, data)


@router.get(
    "/",
    response_model=SupportTicketListResponse,
)
def list_tickets(
    customer_id: int | None = Query(default=None, gt=0),
    status_value: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    category: TicketCategory | None = None,
    outage_id: int | None = Query(default=None, gt=0),
    search: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    return service.list_tickets(
        db,
        customer_id=customer_id,
        status_value=status_value,
        priority=priority,
        category=category,
        outage_id=outage_id,
        search=search,
        page=page,
        limit=limit,
    )


@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [
                UserRole.SUPER_ADMIN,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SUPPORT_AGENT,
                UserRole.NETWORK_ENGINEER,
                UserRole.FIELD_TECHNICIAN,
                UserRole.CUSTOMER,
            ]
        )
    ),
):
    return service.get_ticket(db, ticket_id)


@router.put(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def update_ticket(
    ticket_id: int,
    data: SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [
                UserRole.SUPER_ADMIN,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SUPPORT_AGENT,
                UserRole.NETWORK_ENGINEER,
            ]
        )
    ),
):
    return service.update_ticket(
        db,
        ticket_id,
        data,
    )


@router.patch(
    "/{ticket_id}/status",
    response_model=SupportTicketResponse,
)
def update_ticket_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [
                UserRole.SUPER_ADMIN,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SUPPORT_AGENT,
                UserRole.NETWORK_ENGINEER,
                UserRole.FIELD_TECHNICIAN,
            ]
        )
    ),
):
    return service.update_status(
        db,
        ticket_id,
        data,
    )


@router.patch(
    "/{ticket_id}/resolve",
    response_model=SupportTicketResponse,
)
def resolve_ticket(
    ticket_id: int,
    data: TicketResolution,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [
                UserRole.SUPER_ADMIN,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SUPPORT_AGENT,
                UserRole.NETWORK_ENGINEER,
                UserRole.FIELD_TECHNICIAN,
            ]
        )
    ),
):
    return service.resolve_ticket(
        db,
        ticket_id,
        data,
    )


@router.patch(
    "/{ticket_id}/cancel",
    response_model=SupportTicketResponse,
)
def cancel_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [
                UserRole.SUPER_ADMIN,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SUPPORT_AGENT,
            ]
        )
    ),
):
    return service.cancel_ticket(
        db,
        ticket_id,
    )