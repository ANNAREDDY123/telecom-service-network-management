from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.field_technician import (
    FieldTechnician,
    TechnicianAvailability,
    TechnicianStatus,
)
from app.models.support_ticket import (
    SupportTicket,
    TicketStatus,
)
from app.models.user import User, UserRole
from app.models.ticket_assignment import (
    AssignmentStatus,
    AssignmentType,
    TicketAssignment,
)
from app.repositories.ticket_assignment_repository import (
    TicketAssignmentRepository,
)
from app.schemas.ticket_assignment import (
    AssignmentStatusUpdate,
    TicketAssignmentCreate,
    TicketAssignmentUpdate,
)


class TicketAssignmentService:

    def __init__(self):
        self.repository = TicketAssignmentRepository()

    def get_assignment(
        self,
        db: Session,
        assignment_id: int,
    ) -> TicketAssignment:

        assignment = self.repository.get_by_id(
            db,
            assignment_id,
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket assignment not found",
            )

        return assignment

    def create_assignment(
        self,
        db: Session,
        data: TicketAssignmentCreate,
    ) -> TicketAssignment:

        ticket = db.get(
            SupportTicket,
            data.ticket_id,
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        ticket_status = TicketStatus(ticket.status)

        if ticket_status in {
            TicketStatus.CLOSED,
            TicketStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Closed or cancelled ticket cannot be assigned",
            )

        user = db.get(
            User,
            data.assigned_user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user cannot be assigned",
            )

        if data.assignment_type == AssignmentType.SUPPORT_AGENT:
            if user.role != UserRole.SUPPORT_AGENT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User must have Support Agent role",
                )

        elif data.assignment_type == AssignmentType.FIELD_TECHNICIAN:
            if user.role != UserRole.FIELD_TECHNICIAN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User must have Field Technician role",
                )

            technician = (
                db.query(FieldTechnician)
                .filter(
                    FieldTechnician.user_id == user.id
                )
                .first()
            )

            if not technician:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Field technician profile not found",
                )

            if not technician.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive field technician cannot be assigned",
                )

            if technician.status != TechnicianStatus.AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field technician is not available",
                )

            if technician.availability != TechnicianAvailability.AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field technician is currently unavailable",
                )

        active_assignment = self.repository.get_active_assignment(
            db,
            data.ticket_id,
        )

        if active_assignment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ticket already has an active assignment",
            )

        assignment = TicketAssignment(
            ticket_id=data.ticket_id,
            assigned_user_id=data.assigned_user_id,
            assignment_type=data.assignment_type,
            status=AssignmentStatus.ASSIGNED,
            notes=data.notes.strip() if data.notes else None,
        )

        return self.repository.create(
            db,
            assignment,
        )

    def update_assignment(
        self,
        db: Session,
        assignment_id: int,
        data: TicketAssignmentUpdate,
    ) -> TicketAssignment:

        assignment = self.get_assignment(
            db,
            assignment_id,
        )

        current_status = AssignmentStatus(
            assignment.status
        )

        if current_status in {
            AssignmentStatus.COMPLETED,
            AssignmentStatus.REASSIGNED,
            AssignmentStatus.UNASSIGNED,
            AssignmentStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed or inactive assignment cannot be updated",
            )

        if data.notes is not None:
            assignment.notes = data.notes.strip()

        return self.repository.update(
            db,
            assignment,
        )

    def update_status(
        self,
        db: Session,
        assignment_id: int,
        data: AssignmentStatusUpdate,
    ) -> TicketAssignment:

        assignment = self.get_assignment(
            db,
            assignment_id,
        )

        current = AssignmentStatus(
            assignment.status
        )

        new_status = data.status

        if current == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment is already in the requested status",
            )

        allowed_transitions = {
            AssignmentStatus.ASSIGNED: {
                AssignmentStatus.ACCEPTED,
                AssignmentStatus.IN_PROGRESS,
                AssignmentStatus.REASSIGNED,
                AssignmentStatus.UNASSIGNED,
                AssignmentStatus.CANCELLED,
            },
            AssignmentStatus.ACCEPTED: {
                AssignmentStatus.IN_PROGRESS,
                AssignmentStatus.REASSIGNED,
                AssignmentStatus.UNASSIGNED,
                AssignmentStatus.CANCELLED,
            },
            AssignmentStatus.IN_PROGRESS: {
                AssignmentStatus.COMPLETED,
                AssignmentStatus.REASSIGNED,
                AssignmentStatus.UNASSIGNED,
                AssignmentStatus.CANCELLED,
            },
            AssignmentStatus.COMPLETED: set(),
            AssignmentStatus.REASSIGNED: set(),
            AssignmentStatus.UNASSIGNED: set(),
            AssignmentStatus.CANCELLED: set(),
        }

        if new_status not in allowed_transitions.get(
            current,
            set(),
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid assignment status transition: "
                    f"{current.value} -> {new_status.value}"
                ),
            )

        now = datetime.utcnow()

        if new_status == AssignmentStatus.ACCEPTED:
            assignment.accepted_at = now

        if new_status == AssignmentStatus.IN_PROGRESS:
            if assignment.started_at is None:
                assignment.started_at = now

        if new_status == AssignmentStatus.COMPLETED:
            assignment.completed_at = now

        if new_status == AssignmentStatus.UNASSIGNED:
            assignment.unassigned_at = now

        assignment.status = new_status

        return self.repository.update(
            db,
            assignment,
        )

    def reassign(
        self,
        db: Session,
        assignment_id: int,
        data: TicketAssignmentCreate,
    ) -> TicketAssignment:

        old_assignment = self.get_assignment(
            db,
            assignment_id,
        )

        current_status = AssignmentStatus(
            old_assignment.status
        )

        if current_status not in {
            AssignmentStatus.ASSIGNED,
            AssignmentStatus.ACCEPTED,
            AssignmentStatus.IN_PROGRESS,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active assignment can be reassigned",
            )

        if old_assignment.ticket_id != data.ticket_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reassignment ticket ID must match existing assignment",
            )

        now = datetime.utcnow()

        old_assignment.status = AssignmentStatus.REASSIGNED
        old_assignment.unassigned_at = now

        self.repository.update(
            db,
            old_assignment,
        )

        return self.create_assignment(
            db,
            data,
        )

    def unassign(
        self,
        db: Session,
        assignment_id: int,
    ) -> TicketAssignment:

        assignment = self.get_assignment(
            db,
            assignment_id,
        )

        current_status = AssignmentStatus(
            assignment.status
        )

        if current_status not in {
            AssignmentStatus.ASSIGNED,
            AssignmentStatus.ACCEPTED,
            AssignmentStatus.IN_PROGRESS,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment is not active",
            )

        assignment.status = AssignmentStatus.UNASSIGNED
        assignment.unassigned_at = datetime.utcnow()

        return self.repository.update(
            db,
            assignment,
        )

    def list_assignments(
        self,
        db: Session,
        *,
        ticket_id: int | None = None,
        assigned_user_id: int | None = None,
        assignment_type: AssignmentType | None = None,
        status_value: AssignmentStatus | None = None,
        page: int = 1,
        limit: int = 20,
    ):

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than 0",
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100",
            )

        items, total = self.repository.list_assignments(
            db,
            ticket_id=ticket_id,
            assigned_user_id=assigned_user_id,
            assignment_type=assignment_type,
            status=status_value,
            page=page,
            limit=limit,
        )

        pages = (
            (total + limit - 1) // limit
            if total
            else 0
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }