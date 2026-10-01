from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.ticket_assignment import (
    AssignmentStatus,
    AssignmentType,
    TicketAssignment,
)


class TicketAssignmentRepository:

    def get_by_id(
        self,
        db: Session,
        assignment_id: int,
    ) -> TicketAssignment | None:
        return db.get(TicketAssignment, assignment_id)

    def get_active_assignment(
        self,
        db: Session,
        ticket_id: int,
    ) -> TicketAssignment | None:
        return (
            db.query(TicketAssignment)
            .filter(
                TicketAssignment.ticket_id == ticket_id,
                TicketAssignment.status.in_(
                    [
                        AssignmentStatus.ASSIGNED,
                        AssignmentStatus.ACCEPTED,
                        AssignmentStatus.IN_PROGRESS,
                    ]
                ),
            )
            .order_by(TicketAssignment.assigned_at.desc())
            .first()
        )

    def create(
        self,
        db: Session,
        assignment: TicketAssignment,
    ) -> TicketAssignment:
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def update(
        self,
        db: Session,
        assignment: TicketAssignment,
    ) -> TicketAssignment:
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def list_assignments(
        self,
        db: Session,
        *,
        ticket_id: int | None = None,
        assigned_user_id: int | None = None,
        assignment_type: AssignmentType | None = None,
        status: AssignmentStatus | None = None,
        page: int = 1,
        limit: int = 20,
    ):
        query = db.query(TicketAssignment)

        if ticket_id is not None:
            query = query.filter(
                TicketAssignment.ticket_id == ticket_id
            )

        if assigned_user_id is not None:
            query = query.filter(
                TicketAssignment.assigned_user_id == assigned_user_id
            )

        if assignment_type is not None:
            query = query.filter(
                TicketAssignment.assignment_type == assignment_type
            )

        if status is not None:
            query = query.filter(
                TicketAssignment.status == status
            )

        total = query.with_entities(
            func.count(TicketAssignment.id)
        ).scalar() or 0

        items = (
            query
            .order_by(TicketAssignment.assigned_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return items, total