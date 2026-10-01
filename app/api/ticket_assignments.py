from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.ticket_assignment import (
    AssignmentStatus,
    AssignmentType,
)
from app.schemas.ticket_assignment import (
    AssignmentStatusUpdate,
    TicketAssignmentCreate,
    TicketAssignmentListResponse,
    TicketAssignmentResponse,
    TicketAssignmentUpdate,
)
from app.services.ticket_assignment_service import (
    TicketAssignmentService,
)
from app.utils.dependencies import get_current_user, get_db

from app.models.user import User, UserRole


router = APIRouter(
    prefix="/ticket-assignments",
    tags=["Ticket Assignments"],
)

service = TicketAssignmentService()

MANAGEMENT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
    UserRole.NETWORK_ENGINEER,
    UserRole.FIELD_TECHNICIAN,
}


def require_management_role(user: User):
    if user.role not in MANAGEMENT_ROLES:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


@router.post(
    "/",
    response_model=TicketAssignmentResponse,
)
def create_assignment(
    data: TicketAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_management_role(current_user)

    return service.create_assignment(
        db,
        data,
    )


@router.get(
    "/",
    response_model=TicketAssignmentListResponse,
)
def list_assignments(
    ticket_id: int | None = Query(default=None, gt=0),
    assigned_user_id: int | None = Query(default=None, gt=0),
    assignment_type: AssignmentType | None = None,
    status_value: AssignmentStatus | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_management_role(current_user)

    return service.list_assignments(
        db,
        ticket_id=ticket_id,
        assigned_user_id=assigned_user_id,
        assignment_type=assignment_type,
        status_value=status_value,
        page=page,
        limit=limit,
    )


@router.get(
    "/{assignment_id}",
    response_model=TicketAssignmentResponse,
)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_management_role(current_user)

    return service.get_assignment(
        db,
        assignment_id,
    )


@router.put(
    "/{assignment_id}",
    response_model=TicketAssignmentResponse,
)
def update_assignment(
    assignment_id: int,
    data: TicketAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_management_role(current_user)

    return service.update_assignment(
        db,
        assignment_id,
        data,
    )


@router.patch(
    "/{assignment_id}/status",
    response_model=TicketAssignmentResponse,
)
def update_assignment_status(
    assignment_id: int,
    data: AssignmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_management_role(current_user)

    return service.update_status(
        db,
        assignment_id,
        data,
    )


@router.patch(
    "/{assignment_id}/unassign",
    response_model=TicketAssignmentResponse,
)
def unassign_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_management_role(current_user)

    return service.unassign(
        db,
        assignment_id,
    )


@router.post(
    "/{assignment_id}/reassign",
    response_model=TicketAssignmentResponse,
)
def reassign_assignment(
    assignment_id: int,
    data: TicketAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_management_role(current_user)

    return service.reassign(
        db,
        assignment_id,
        data,
    )