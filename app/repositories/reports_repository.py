from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.customer import Customer, KYCStatus
from app.models.field_technician import (
    FieldTechnician,
    TechnicianAvailability,
    TechnicianStatus,
)
from app.models.network_outage import (
    NetworkOutage,
    OutageStatus,
)
from app.models.network_tower import (
    NetworkTower,
    TowerStatus,
)
from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
)
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
)
from app.models.support_ticket import (
    SupportTicket,
    TicketPriority,
    TicketStatus,
)
from app.models.ticket_assignment import (
    AssignmentStatus,
    AssignmentType,
    TicketAssignment,
)
from app.models.usage import (
    Usage,
    UsageStatus,
    UsageType,
)
from app.models.sla_tracking import SLATracking


class ReportsRepository:
    def __init__(self, db: Session):
        self.db = db

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _start_datetime(value: date | None) -> datetime | None:
        if value is None:
            return None

        return datetime.combine(value, time.min)

    @staticmethod
    def _end_datetime(value: date | None) -> datetime | None:
        if value is None:
            return None

        return datetime.combine(value, time.max)

    # ========================================================
    # CUSTOMER REPORT
    # ========================================================

    def get_customer_summary(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:

        customer_query = self.db.query(Customer)

        if start_date:
            customer_query = customer_query.filter(
                Customer.created_at
                >= self._start_datetime(start_date)
            )

        if end_date:
            customer_query = customer_query.filter(
                Customer.created_at
                <= self._end_datetime(end_date)
            )

        customers = customer_query.all()

        total_customers = len(customers)

        active_customers = sum(
            1 for customer in customers
            if customer.is_active
        )

        inactive_customers = (
            total_customers - active_customers
        )

        verified_kyc_customers = sum(
            1
            for customer in customers
            if customer.kyc_status == KYCStatus.VERIFIED
        )

        pending_kyc_customers = sum(
            1
            for customer in customers
            if customer.kyc_status == KYCStatus.PENDING
        )

        rejected_kyc_customers = sum(
            1
            for customer in customers
            if customer.kyc_status == KYCStatus.REJECTED
        )

        subscription_query = self.db.query(
            func.count(Subscription.id)
        ).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        )

        if start_date:
            subscription_query = subscription_query.filter(
                Subscription.start_date >= start_date
            )

        if end_date:
            subscription_query = subscription_query.filter(
                Subscription.start_date <= end_date
            )

        active_subscriptions = (
            subscription_query.scalar() or 0
        )

        active_sims = (
            self.db.query(Subscription)
            .filter(
                Subscription.status
                == SubscriptionStatus.ACTIVE
            )
            .count()
        )

        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "inactive_customers": inactive_customers,
            "verified_kyc_customers": verified_kyc_customers,
            "pending_kyc_customers": pending_kyc_customers,
            "rejected_kyc_customers": rejected_kyc_customers,
            "active_subscriptions": active_subscriptions,
            "active_sims": active_sims,
        }

    # ========================================================
    # USAGE REPORT
    # ========================================================

    def get_usage_report(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        subscription_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], Decimal, int]:

        query = (
            self.db.query(
                Usage,
                Customer,
                Subscription,
            )
            .join(
                Customer,
                Usage.customer_id == Customer.id,
            )
            .join(
                Subscription,
                Usage.subscription_id == Subscription.id,
            )
            .filter(
                Usage.usage_type == UsageType.DATA.value,
                Usage.status.in_(
                    [
                        UsageStatus.RECORDED.value,
                        UsageStatus.PROCESSED.value,
                    ]
                ),
            )
        )

        if start_date:
            query = query.filter(
                Usage.usage_date >= start_date
            )

        if end_date:
            query = query.filter(
                Usage.usage_date <= end_date
            )

        if customer_id:
            query = query.filter(
                Usage.customer_id == customer_id
            )

        if plan_id:
            query = query.filter(
                Subscription.plan_id == plan_id
            )

        if subscription_id:
            query = query.filter(
                Usage.subscription_id == subscription_id
            )

        total_records = query.count()

        rows = (
            query.order_by(Usage.usage_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        total_usage = (
            query.with_entities(
                func.coalesce(
                    func.sum(Usage.data_used_mb),
                    0,
                )
            ).scalar()
            or 0
        )

        items = []

        for usage, customer, subscription in rows:
            plan = subscription.plan

            items.append(
                {
                    "customer_id": customer.id,
                    "customer_number": customer.customer_number,
                    "customer_name": customer.full_name,
                    "subscription_id": subscription.id,
                    "plan_id": (
                        plan.id if plan else None
                    ),
                    "plan_code": (
                        plan.plan_code if plan else None
                    ),
                    "plan_name": (
                        plan.plan_name if plan else None
                    ),
                    "data_used_mb": (
                        usage.data_used_mb or Decimal("0")
                    ),
                }
            )

        return items, Decimal(str(total_usage)), total_records

    # ========================================================
    # NETWORK REPORT
    # ========================================================

    def get_network_report(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        tower_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:

        tower_query = self.db.query(NetworkTower)

        total_towers = tower_query.count()

        active_towers = tower_query.filter(
            NetworkTower.status == TowerStatus.ACTIVE.value
        ).count()

        maintenance_towers = tower_query.filter(
            NetworkTower.status
            == TowerStatus.MAINTENANCE.value
        ).count()

        inactive_towers = tower_query.filter(
            NetworkTower.status
            == TowerStatus.INACTIVE.value
        ).count()

        outage_query = (
            self.db.query(
                NetworkOutage,
                NetworkTower,
            )
            .join(
                NetworkTower,
                NetworkOutage.tower_id
                == NetworkTower.id,
            )
        )

        if start_date:
            outage_query = outage_query.filter(
                NetworkOutage.start_time
                >= self._start_datetime(start_date)
            )

        if end_date:
            outage_query = outage_query.filter(
                NetworkOutage.start_time
                <= self._end_datetime(end_date)
            )

        if tower_id:
            outage_query = outage_query.filter(
                NetworkOutage.tower_id == tower_id
            )

        if status:
            outage_query = outage_query.filter(
                NetworkOutage.status == status
            )

        total_outages = outage_query.count()

        active_outages = outage_query.filter(
            ~NetworkOutage.status.in_(
                [
                    OutageStatus.RESTORED.value,
                    OutageStatus.CLOSED.value,
                    OutageStatus.CANCELLED.value,
                ]
            )
        ).count()

        restored_outages = outage_query.filter(
            NetworkOutage.status
            == OutageStatus.RESTORED.value
        ).count()

        rows = (
            outage_query
            .order_by(NetworkOutage.start_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        outage_items = []
        total_duration = 0.0

        for outage, tower in rows:
            duration_minutes = None

            if outage.actual_restore_time:
                duration = (
                    outage.actual_restore_time
                    - outage.start_time
                )

                duration_minutes = (
                    duration.total_seconds() / 60
                )

                total_duration += duration_minutes

            outage_items.append(
                {
                    "outage_id": outage.id,
                    "outage_number": outage.outage_number,
                    "tower_id": tower.id,
                    "tower_code": tower.tower_code,
                    "status": (
                        outage.status.value
                        if hasattr(outage.status, "value")
                        else outage.status
                    ),
                    "severity": (
                        outage.severity.value
                        if hasattr(outage.severity, "value")
                        else outage.severity
                    ),
                    "started_at": outage.start_time,
                    "restored_at": outage.actual_restore_time,
                    "duration_minutes": duration_minutes,
                }
            )

        return {
            "total_towers": total_towers,
            "active_towers": active_towers,
            "maintenance_towers": maintenance_towers,
            "inactive_towers": inactive_towers,
            "total_outages": total_outages,
            "active_outages": active_outages,
            "restored_outages": restored_outages,
            "total_outage_duration_minutes": total_duration,
            "outages": outage_items,
            "page": page,
            "page_size": page_size,
            "total_pages": (
                (total_outages + page_size - 1)
                // page_size
                if total_outages
                else 0
            ),
        }

    # ========================================================
    # SUPPORT / SLA REPORT
    # ========================================================

    def get_support_report(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:

        query = self.db.query(SupportTicket)

        if start_date:
            query = query.filter(
                SupportTicket.created_at
                >= self._start_datetime(start_date)
            )

        if end_date:
            query = query.filter(
                SupportTicket.created_at
                <= self._end_datetime(end_date)
            )

        if customer_id:
            query = query.filter(
                SupportTicket.customer_id == customer_id
            )

        if status:
            query = query.filter(
                SupportTicket.status == status
            )

        total_tickets = query.count()

        open_tickets = query.filter(
            SupportTicket.status
            == TicketStatus.OPEN.value
        ).count()

        in_progress_tickets = query.filter(
            SupportTicket.status
            == TicketStatus.IN_PROGRESS.value
        ).count()

        resolved_tickets = query.filter(
            SupportTicket.status
            == TicketStatus.RESOLVED.value
        ).count()

        closed_tickets = query.filter(
            SupportTicket.status
            == TicketStatus.CLOSED.value
        ).count()

        cancelled_tickets = query.filter(
            SupportTicket.status
            == TicketStatus.CANCELLED.value
        ).count()

        high_priority_tickets = query.filter(
            SupportTicket.priority
            == TicketPriority.HIGH.value
        ).count()

        sla_query = (
            self.db.query(SLATracking)
            .join(
                SupportTicket,
                SLATracking.ticket_id
                == SupportTicket.id,
            )
        )

        if start_date:
            sla_query = sla_query.filter(
                SupportTicket.created_at
                >= self._start_datetime(start_date)
            )

        if end_date:
            sla_query = sla_query.filter(
                SupportTicket.created_at
                <= self._end_datetime(end_date)
            )

        if customer_id:
            sla_query = sla_query.filter(
                SupportTicket.customer_id == customer_id
            )

        sla_breaches = sla_query.filter(
            or_(
                SLATracking.response_breached.is_(True),
                SLATracking.resolution_breached.is_(True),
            )
        ).count()

        response_breaches = sla_query.filter(
            SLATracking.response_breached.is_(True)
        ).count()

        resolution_breaches = sla_query.filter(
            SLATracking.resolution_breached.is_(True)
        ).count()

        rows = (
            query.order_by(
                SupportTicket.created_at.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        tickets = []

        resolution_times = []
        response_times = []

        for ticket in rows:
            resolution_minutes = None

            if ticket.resolved_at:
                resolution_minutes = (
                    ticket.resolved_at
                    - ticket.created_at
                ).total_seconds() / 60

                resolution_times.append(
                    resolution_minutes
                )

            sla = ticket.sla_tracking

            if sla and sla.response_at:
                response_minutes = (
                    sla.response_at
                    - ticket.created_at
                ).total_seconds() / 60

                response_times.append(
                    response_minutes
                )

            sla_status = None

            if sla:
                sla_status = (
                    sla.status.value
                    if hasattr(sla.status, "value")
                    else sla.status
                )

            tickets.append(
                {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "customer_id": ticket.customer_id,
                    "category": (
                        ticket.category.value
                        if hasattr(ticket.category, "value")
                        else ticket.category
                    ),
                    "priority": (
                        ticket.priority.value
                        if hasattr(ticket.priority, "value")
                        else ticket.priority
                    ),
                    "status": (
                        ticket.status.value
                        if hasattr(ticket.status, "value")
                        else ticket.status
                    ),
                    "source": (
                        ticket.source.value
                        if hasattr(ticket.source, "value")
                        else ticket.source
                    ),
                    "created_at": ticket.created_at,
                    "resolved_at": ticket.resolved_at,
                    "resolution_minutes": resolution_minutes,
                    "sla_status": sla_status,
                }
            )

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets,
            "cancelled_tickets": cancelled_tickets,
            "high_priority_tickets": high_priority_tickets,
            "sla_breaches": sla_breaches,
            "response_breaches": response_breaches,
            "resolution_breaches": resolution_breaches,
            "average_resolution_minutes": (
                sum(resolution_times)
                / len(resolution_times)
                if resolution_times
                else None
            ),
            "average_response_minutes": (
                sum(response_times)
                / len(response_times)
                if response_times
                else None
            ),
            "tickets": tickets,
            "page": page,
            "page_size": page_size,
            "total_pages": (
                (total_tickets + page_size - 1)
                // page_size
                if total_tickets
                else 0
            ),
        }

    # ========================================================
    # TECHNICIAN REPORT
    # ========================================================

    def get_technician_report(
        self,
        technician_id: int | None = None,
        status: str | None = None,
    ) -> dict:

        query = self.db.query(FieldTechnician).filter(
            FieldTechnician.is_active.is_(True)
        )

        if technician_id:
            query = query.filter(
                FieldTechnician.id == technician_id
            )

        if status:
            query = query.filter(
                FieldTechnician.status == status
            )

        technicians = query.all()

        total_technicians = len(technicians)

        available_technicians = sum(
            1
            for technician in technicians
            if (
                technician.status
                == TechnicianStatus.AVAILABLE.value
                and technician.availability
                == TechnicianAvailability.AVAILABLE.value
            )
        )

        busy_technicians = sum(
            1
            for technician in technicians
            if technician.status
            == TechnicianStatus.BUSY.value
        )

        technician_items = []

        total_assignments = 0
        completed_assignments = 0

        for technician in technicians:
            assignments = (
                self.db.query(TicketAssignment)
                .filter(
                    TicketAssignment.assigned_user_id
                    == technician.user_id,
                    TicketAssignment.assignment_type
                    == AssignmentType.FIELD_TECHNICIAN.value,
                )
                .all()
            )

            technician_total = len(assignments)

            active_count = sum(
                1
                for assignment in assignments
                if assignment.status
                in {
                    AssignmentStatus.ASSIGNED.value,
                    AssignmentStatus.ACCEPTED.value,
                    AssignmentStatus.IN_PROGRESS.value,
                }
            )

            completed_count = sum(
                1
                for assignment in assignments
                if assignment.status
                == AssignmentStatus.COMPLETED.value
            )

            cancelled_count = sum(
                1
                for assignment in assignments
                if assignment.status
                == AssignmentStatus.CANCELLED.value
            )

            completion_rate = (
                completed_count
                / technician_total
                * 100
                if technician_total
                else 0.0
            )

            technician_name = (
                technician.user.full_name
                if technician.user
                else technician.technician_code
            )

            technician_items.append(
                {
                    "technician_id": technician.id,
                    "technician_code": technician.technician_code,
                    "technician_name": technician_name,
                    "status": (
                        technician.status.value
                        if hasattr(technician.status, "value")
                        else technician.status
                    ),
                    "availability": (
                        technician.availability.value
                        if hasattr(
                            technician.availability,
                            "value",
                        )
                        else technician.availability
                    ),
                    "total_assignments": technician_total,
                    "active_assignments": active_count,
                    "completed_assignments": completed_count,
                    "cancelled_assignments": cancelled_count,
                    "completion_rate": completion_rate,
                }
            )

            total_assignments += technician_total
            completed_assignments += completed_count

        overall_completion_rate = (
            completed_assignments
            / total_assignments
            * 100
            if total_assignments
            else 0.0
        )

        return {
            "total_technicians": total_technicians,
            "available_technicians": available_technicians,
            "busy_technicians": busy_technicians,
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "overall_completion_rate": overall_completion_rate,
            "technicians": technician_items,
        }

    # ========================================================
    # EXECUTIVE OVERVIEW
    # ========================================================

    def get_overview(self) -> dict:

        customers = self.get_customer_summary()

        total_usage = (
            self.db.query(
                func.coalesce(
                    func.sum(Usage.data_used_mb),
                    0,
                )
            )
            .filter(
                Usage.usage_type == UsageType.DATA.value,
                Usage.status.in_(
                    [
                        UsageStatus.RECORDED.value,
                        UsageStatus.PROCESSED.value,
                    ]
                ),
            )
            .scalar()
            or 0
        )

        active_subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.status
                == SubscriptionStatus.ACTIVE
            )
            .count()
        )

        active_sims = (
            self.db.query(Subscription)
            .filter(
                Subscription.status
                == SubscriptionStatus.ACTIVE
            )
            .count()
        )

        total_towers = (
            self.db.query(NetworkTower).count()
        )

        active_outages = (
            self.db.query(NetworkOutage)
            .filter(
                ~NetworkOutage.status.in_(
                    [
                        OutageStatus.RESTORED.value,
                        OutageStatus.CLOSED.value,
                        OutageStatus.CANCELLED.value,
                    ]
                )
            )
            .count()
        )

        total_tickets = (
            self.db.query(SupportTicket).count()
        )

        open_tickets = (
            self.db.query(SupportTicket)
            .filter(
                SupportTicket.status.in_(
                    [
                        TicketStatus.OPEN.value,
                        TicketStatus.IN_PROGRESS.value,
                        TicketStatus.PENDING_CUSTOMER.value,
                    ]
                )
            )
            .count()
        )

        sla_breaches = (
            self.db.query(SLATracking)
            .filter(
                or_(
                    SLATracking.response_breached.is_(True),
                    SLATracking.resolution_breached.is_(True),
                ),
                SLATracking.status != "Completed",
            )
            .count()
        )

        total_service_requests = (
            self.db.query(ServiceRequest).count()
        )

        completed_service_requests = (
            self.db.query(ServiceRequest)
            .filter(
                ServiceRequest.status
                == ServiceRequestStatus.COMPLETED
            )
            .count()
        )

        technician_report = (
            self.get_technician_report()
        )

        return {
            "report_generated_at": datetime.utcnow(),
            "customers": customers,
            "total_data_usage_mb": Decimal(
                str(total_usage)
            ),
            "active_subscriptions": active_subscriptions,
            "active_sims": active_sims,
            "total_towers": total_towers,
            "active_outages": active_outages,
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "sla_breaches": sla_breaches,
            "total_service_requests": total_service_requests,
            "completed_service_requests": (
                completed_service_requests
            ),
            "total_technicians": (
                technician_report["total_technicians"]
            ),
            "available_technicians": (
                technician_report["available_technicians"]
            ),
            "busy_technicians": (
                technician_report["busy_technicians"]
            ),
        }