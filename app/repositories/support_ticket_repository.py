from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.support_ticket import (
    SupportTicket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


class SupportTicketRepository:

    def get_by_id(
        self,
        db: Session,
        ticket_id: int,
    ) -> SupportTicket | None:
        return db.get(SupportTicket, ticket_id)

    def get_by_number(
        self,
        db: Session,
        ticket_number: str,
    ) -> SupportTicket | None:
        statement = select(SupportTicket).where(
            SupportTicket.ticket_number == ticket_number
        )

        return db.scalar(statement)

    def create(
        self,
        db: Session,
        ticket: SupportTicket,
    ) -> SupportTicket:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return ticket

    def update(
        self,
        db: Session,
        ticket: SupportTicket,
    ) -> SupportTicket:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return ticket

    def list_tickets(
        self,
        db: Session,
        *,
        customer_id: int | None = None,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        category: TicketCategory | None = None,
        outage_id: int | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[SupportTicket], int]:

        statement = select(SupportTicket)

        if customer_id is not None:
            statement = statement.where(
                SupportTicket.customer_id == customer_id
            )

        if status is not None:
            statement = statement.where(
                SupportTicket.status == status
            )

        if priority is not None:
            statement = statement.where(
                SupportTicket.priority == priority
            )

        if category is not None:
            statement = statement.where(
                SupportTicket.category == category
            )

        if outage_id is not None:
            statement = statement.where(
                SupportTicket.outage_id == outage_id
            )

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    SupportTicket.ticket_number.ilike(search_value),
                    SupportTicket.title.ilike(search_value),
                    SupportTicket.description.ilike(search_value),
                )
            )

        count_statement = select(
            func.count()
        ).select_from(
            statement.subquery()
        )

        total = db.scalar(count_statement) or 0

        statement = (
            statement
            .order_by(SupportTicket.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        items = list(db.scalars(statement).all())

        return items, total