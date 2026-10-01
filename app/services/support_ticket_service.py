from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.network_outage import NetworkOutage
from app.models.support_ticket import (
    SupportTicket,
    TicketPriority,
    TicketStatus,
)
from app.repositories.support_ticket_repository import (
    SupportTicketRepository,
)
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketUpdate,
    TicketResolution,
    TicketStatusUpdate,
)


class SupportTicketService:

    def __init__(self):
        self.repository = SupportTicketRepository()

    def create_ticket(
        self,
        db: Session,
        data: SupportTicketCreate,
    ) -> SupportTicket:

        customer = db.get(Customer, data.customer_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive customer cannot create support ticket",
            )

        existing = self.repository.get_by_number(
            db,
            data.ticket_number,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ticket number already exists",
            )

        if data.outage_id is not None:
            outage = db.get(
                NetworkOutage,
                data.outage_id,
            )

            if not outage:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Network outage not found",
                )

        ticket = SupportTicket(
            ticket_number=data.ticket_number,
            customer_id=data.customer_id,
            outage_id=data.outage_id,
            title=data.title.strip(),
            description=data.description.strip(),
            category=data.category,
            priority=data.priority,
            status=TicketStatus.OPEN,
            source=data.source,
        )

        return self.repository.create(db, ticket)

    def get_ticket(
        self,
        db: Session,
        ticket_id: int,
    ) -> SupportTicket:

        ticket = self.repository.get_by_id(
            db,
            ticket_id,
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )

        return ticket

    def update_ticket(
        self,
        db: Session,
        ticket_id: int,
        data: SupportTicketUpdate,
    ) -> SupportTicket:

        ticket = self.get_ticket(db, ticket_id)

        current_status = TicketStatus(ticket.status)

        if current_status in {
            TicketStatus.CLOSED,
            TicketStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Closed or cancelled ticket cannot be updated",
            )

        if data.outage_id is not None:
            outage = db.get(
                NetworkOutage,
                data.outage_id,
            )

            if not outage:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Network outage not found",
                )

            ticket.outage_id = data.outage_id

        if data.title is not None:
            ticket.title = data.title.strip()

        if data.description is not None:
            ticket.description = data.description.strip()

        if data.category is not None:
            ticket.category = data.category

        if data.priority is not None:
            ticket.priority = data.priority

        if data.source is not None:
            ticket.source = data.source

        return self.repository.update(db, ticket)

    def update_status(
        self,
        db: Session,
        ticket_id: int,
        data: TicketStatusUpdate,
    ) -> SupportTicket:

        ticket = self.get_ticket(db, ticket_id)

        # Database stores the status as a string.
        # Convert it back to the TicketStatus enum before
        # performing transition validation.
        current = TicketStatus(ticket.status)
        new_status = data.status

        if current == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket is already in the requested status",
            )

        allowed_transitions = {
            TicketStatus.OPEN: {
                TicketStatus.IN_PROGRESS,
                TicketStatus.PENDING_CUSTOMER,
                TicketStatus.CANCELLED,
            },
            TicketStatus.IN_PROGRESS: {
                TicketStatus.PENDING_CUSTOMER,
                TicketStatus.RESOLVED,
                TicketStatus.CANCELLED,
            },
            TicketStatus.PENDING_CUSTOMER: {
                TicketStatus.IN_PROGRESS,
                TicketStatus.RESOLVED,
                TicketStatus.CANCELLED,
            },
            TicketStatus.RESOLVED: {
                TicketStatus.CLOSED,
                TicketStatus.IN_PROGRESS,
            },
            TicketStatus.CLOSED: set(),
            TicketStatus.CANCELLED: set(),
        }

        if new_status not in allowed_transitions.get(
            current,
            set(),
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid ticket status transition: "
                    f"{current.value} -> {new_status.value}"
                ),
            )

        # Closing is allowed only after the ticket has been resolved.
        if new_status == TicketStatus.CLOSED:
            if ticket.resolved_at is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ticket must be resolved before closing",
                )

        ticket.status = new_status

        if new_status == TicketStatus.CANCELLED:
            ticket.cancelled_at = datetime.utcnow()

        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()

        if new_status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()

        return self.repository.update(db, ticket)

    def resolve_ticket(
        self,
        db: Session,
        ticket_id: int,
        data: TicketResolution,
    ) -> SupportTicket:

        ticket = self.get_ticket(db, ticket_id)

        current_status = TicketStatus(ticket.status)

        if current_status in {
            TicketStatus.CLOSED,
            TicketStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Closed or cancelled ticket cannot be resolved",
            )

        if current_status == TicketStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket is already resolved",
            )

        ticket.resolution_notes = data.resolution_notes.strip()
        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = datetime.utcnow()

        return self.repository.update(db, ticket)

    def cancel_ticket(
        self,
        db: Session,
        ticket_id: int,
    ) -> SupportTicket:

        ticket = self.get_ticket(db, ticket_id)

        current_status = TicketStatus(ticket.status)

        if current_status in {
            TicketStatus.CLOSED,
            TicketStatus.CANCELLED,
            TicketStatus.RESOLVED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket cannot be cancelled from its current status",
            )

        ticket.status = TicketStatus.CANCELLED
        ticket.cancelled_at = datetime.utcnow()

        return self.repository.update(db, ticket)

    def list_tickets(
        self,
        db: Session,
        *,
        customer_id: int | None = None,
        status_value: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        category=None,
        outage_id: int | None = None,
        search: str | None = None,
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

        items, total = self.repository.list_tickets(
            db,
            customer_id=customer_id,
            status=status_value,
            priority=priority,
            category=category,
            outage_id=outage_id,
            search=search,
            page=page,
            limit=limit,
        )

        pages = (total + limit - 1) // limit if total else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }