from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.sla_policy import SLAPolicy, SLAPriority, SLAStatus
from app.models.sla_tracking import SLATracking, SLATrackingStatus


class SLARepository:
    # =========================
    # SLA POLICY
    # =========================

    @staticmethod
    def get_policy(
        db: Session,
        policy_id: int,
    ) -> SLAPolicy | None:
        return (
            db.query(SLAPolicy)
            .filter(SLAPolicy.id == policy_id)
            .first()
        )

    @staticmethod
    def get_policy_by_code(
        db: Session,
        sla_code: str,
    ) -> SLAPolicy | None:
        return (
            db.query(SLAPolicy)
            .filter(SLAPolicy.sla_code == sla_code)
            .first()
        )

    @staticmethod
    def create_policy(
        db: Session,
        policy: SLAPolicy,
    ) -> SLAPolicy:
        db.add(policy)
        db.commit()
        db.refresh(policy)

        return policy

    @staticmethod
    def update_policy(
        db: Session,
        policy: SLAPolicy,
    ) -> SLAPolicy:
        db.add(policy)
        db.commit()
        db.refresh(policy)

        return policy

    @staticmethod
    def list_policies(
        db: Session,
        page: int,
        page_size: int,
        priority: SLAPriority | None = None,
        status: SLAStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[SLAPolicy], int]:

        query = db.query(SLAPolicy)

        if priority is not None:
            query = query.filter(
                SLAPolicy.priority == priority
            )

        if status is not None:
            query = query.filter(
                SLAPolicy.status == status
            )

        if search:
            search_value = f"%{search.strip()}%"

            query = query.filter(
                or_(
                    SLAPolicy.sla_code.ilike(search_value),
                    SLAPolicy.sla_name.ilike(search_value),
                    SLAPolicy.description.ilike(search_value),
                )
            )

        total = query.with_entities(
            func.count(SLAPolicy.id)
        ).scalar() or 0

        offset = (page - 1) * page_size

        items = (
            query
            .order_by(SLAPolicy.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total

    # =========================
    # SLA TRACKING
    # =========================

    @staticmethod
    def get_tracking(
        db: Session,
        tracking_id: int,
    ) -> SLATracking | None:
        return (
            db.query(SLATracking)
            .filter(SLATracking.id == tracking_id)
            .first()
        )

    @staticmethod
    def get_tracking_by_ticket(
        db: Session,
        ticket_id: int,
    ) -> SLATracking | None:
        return (
            db.query(SLATracking)
            .filter(SLATracking.ticket_id == ticket_id)
            .first()
        )

    @staticmethod
    def create_tracking(
        db: Session,
        tracking: SLATracking,
    ) -> SLATracking:
        db.add(tracking)
        db.commit()
        db.refresh(tracking)

        return tracking

    @staticmethod
    def update_tracking(
        db: Session,
        tracking: SLATracking,
    ) -> SLATracking:
        db.add(tracking)
        db.commit()
        db.refresh(tracking)

        return tracking

    @staticmethod
    def list_tracking(
        db: Session,
        page: int,
        page_size: int,
        status: SLATrackingStatus | None = None,
        policy_id: int | None = None,
        ticket_id: int | None = None,
    ) -> tuple[list[SLATracking], int]:

        query = db.query(SLATracking)

        if status is not None:
            query = query.filter(
                SLATracking.status == status
            )

        if policy_id is not None:
            query = query.filter(
                SLATracking.sla_policy_id == policy_id
            )

        if ticket_id is not None:
            query = query.filter(
                SLATracking.ticket_id == ticket_id
            )

        total = query.with_entities(
            func.count(SLATracking.id)
        ).scalar() or 0

        offset = (page - 1) * page_size

        items = (
            query
            .order_by(SLATracking.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total