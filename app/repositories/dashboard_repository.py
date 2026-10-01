from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.customer import Customer
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
)
from app.models.service_plan import ServicePlan
from app.models.service_request import ServiceRequest
from app.models.sim_card import SIMCard, SIMStatus
from app.models.sla_tracking import SLATracking
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
)
from app.models.support_ticket import (
    SupportTicket,
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


class DashboardRepository:
    """
    Repository responsible for dashboard aggregation queries.

    Dashboard data is calculated directly from the database rather
    than being stored as duplicated counters.
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # CUSTOMER METRICS
    # ---------------------------------------------------------

    def get_total_customers(self) -> int:
        return (
            self.db.query(func.count(Customer.id))
            .scalar()
            or 0
        )

    def get_active_customers(self) -> int:
        return (
            self.db.query(func.count(Customer.id))
            .filter(Customer.is_active.is_(True))
            .scalar()
            or 0
        )

    # ---------------------------------------------------------
    # SUBSCRIPTION METRICS
    # ---------------------------------------------------------

    def get_active_subscriptions(self) -> int:
        return (
            self.db.query(func.count(Subscription.id))
            .filter(
                Subscription.status
                == SubscriptionStatus.ACTIVE
            )
            .scalar()
            or 0
        )

    # ---------------------------------------------------------
    # SIM METRICS
    # ---------------------------------------------------------

    def get_active_sims(self) -> int:
        return (
            self.db.query(func.count(SIMCard.id))
            .filter(
                SIMCard.status == SIMStatus.ACTIVE
            )
            .scalar()
            or 0
        )

    # ---------------------------------------------------------
    # USAGE METRICS
    # ---------------------------------------------------------

    def get_total_data_usage_mb(self) -> Decimal:
        value = (
            self.db.query(
                func.coalesce(
                    func.sum(Usage.data_used_mb),
                    0,
                )
            )
            .filter(
                Usage.usage_type
                == UsageType.DATA.value,
                Usage.status.in_(
                    [
                        UsageStatus.RECORDED.value,
                        UsageStatus.PROCESSED.value,
                    ]
                ),
            )
            .scalar()
        )

        return Decimal(str(value or 0))

    # ---------------------------------------------------------
    # OUTAGE METRICS
    # ---------------------------------------------------------

    def get_network_outages(self) -> int:
        """
        Count currently active/non-restored outages.

        Restored, Closed and Cancelled outages are not considered
        active network outages.
        """

        return (
            self.db.query(func.count(NetworkOutage.id))
            .filter(
                NetworkOutage.status.notin_(
                    [
                        OutageStatus.RESTORED,
                        OutageStatus.CLOSED,
                        OutageStatus.CANCELLED,
                    ]
                )
            )
            .scalar()
            or 0
        )

    # ---------------------------------------------------------
    # SUPPORT TICKET METRICS
    # ---------------------------------------------------------

    def get_open_tickets(self) -> int:
        return (
            self.db.query(func.count(SupportTicket.id))
            .filter(
                SupportTicket.status.in_(
                    [
                        TicketStatus.OPEN.value,
                        TicketStatus.IN_PROGRESS.value,
                        TicketStatus.PENDING_CUSTOMER.value,
                    ]
                )
            )
            .scalar()
            or 0
        )

    # ---------------------------------------------------------
    # SLA METRICS
    # ---------------------------------------------------------

    def get_sla_breaches(self) -> int:
        return (
            self.db.query(func.count(SLATracking.id))
            .filter(
                (
                    (SLATracking.response_breached.is_(True))
                    |
                    (SLATracking.resolution_breached.is_(True))
                ),
                SLATracking.status != "Completed",
            )
            .scalar()
            or 0
        )

    # ---------------------------------------------------------
    # TECHNICIAN METRICS
    # ---------------------------------------------------------

    def get_total_technicians(self) -> int:
        return (
            self.db.query(func.count(FieldTechnician.id))
            .filter(
                FieldTechnician.is_active.is_(True)
            )
            .scalar()
            or 0
        )

    def get_available_technicians(self) -> int:
        return (
            self.db.query(func.count(FieldTechnician.id))
            .filter(
                FieldTechnician.is_active.is_(True),
                FieldTechnician.status
                == TechnicianStatus.AVAILABLE.value,
                FieldTechnician.availability
                == TechnicianAvailability.AVAILABLE.value,
            )
            .scalar()
            or 0
        )

    def get_busy_technicians(self) -> int:
        return (
            self.db.query(func.count(FieldTechnician.id))
            .filter(
                FieldTechnician.is_active.is_(True),
                FieldTechnician.status
                == TechnicianStatus.BUSY.value,
            )
            .scalar()
            or 0
        )

    def get_technician_workload(self) -> list[dict]:
        technicians = (
            self.db.query(FieldTechnician)
            .filter(FieldTechnician.is_active.is_(True))
            .order_by(FieldTechnician.id)
            .all()
        )

        result = []

        active_assignment_statuses = [
            AssignmentStatus.ASSIGNED.value,
            AssignmentStatus.ACCEPTED.value,
            AssignmentStatus.IN_PROGRESS.value,
        ]

        for technician in technicians:
            user_id = technician.user_id

            active_assignments = (
                self.db.query(
                    func.count(TicketAssignment.id)
                )
                .filter(
                    TicketAssignment.assigned_user_id
                    == user_id,
                    TicketAssignment.assignment_type
                    == AssignmentType.FIELD_TECHNICIAN.value,
                    TicketAssignment.status.in_(
                        active_assignment_statuses
                    ),
                )
                .scalar()
                or 0
            )

            completed_assignments = (
                self.db.query(
                    func.count(TicketAssignment.id)
                )
                .filter(
                    TicketAssignment.assigned_user_id
                    == user_id,
                    TicketAssignment.assignment_type
                    == AssignmentType.FIELD_TECHNICIAN.value,
                    TicketAssignment.status
                    == AssignmentStatus.COMPLETED.value,
                )
                .scalar()
                or 0
            )

            total_assignments = (
                self.db.query(
                    func.count(TicketAssignment.id)
                )
                .filter(
                    TicketAssignment.assigned_user_id
                    == user_id,
                    TicketAssignment.assignment_type
                    == AssignmentType.FIELD_TECHNICIAN.value,
                )
                .scalar()
                or 0
            )

            technician_name = (
                technician.user.full_name
                if technician.user
                else technician.technician_code
            )

            result.append(
                {
                    "technician_id": technician.id,
                    "technician_code": (
                        technician.technician_code
                    ),
                    "technician_name": technician_name,
                    "status": (
                        technician.status.value
                        if hasattr(
                            technician.status,
                            "value",
                        )
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
                    "active_assignments": active_assignments,
                    "completed_assignments": completed_assignments,
                    "total_assignments": total_assignments,
                }
            )

        return result

    # ---------------------------------------------------------
    # TOWER METRICS
    # ---------------------------------------------------------

    def get_total_towers(self) -> int:
        return (
            self.db.query(func.count(NetworkTower.id))
            .scalar()
            or 0
        )

    def get_tower_status(self) -> list[dict]:
        rows = (
            self.db.query(
                NetworkTower.status,
                func.count(NetworkTower.id),
            )
            .group_by(NetworkTower.status)
            .order_by(NetworkTower.status)
            .all()
        )

        return [
            {
                "status": (
                    status.value
                    if hasattr(status, "value")
                    else status
                ),
                "count": count,
            }
            for status, count in rows
        ]

    # ---------------------------------------------------------
    # SERVICE REQUEST METRICS
    # ---------------------------------------------------------

    def get_total_service_requests(self) -> int:
        return (
            self.db.query(func.count(ServiceRequest.id))
            .scalar()
            or 0
        )

    def get_service_request_status(self) -> list[dict]:
        rows = (
            self.db.query(
                ServiceRequest.status,
                func.count(ServiceRequest.id),
            )
            .group_by(ServiceRequest.status)
            .order_by(ServiceRequest.status)
            .all()
        )

        return [
            {
                "status": (
                    status.value
                    if hasattr(status, "value")
                    else status
                ),
                "count": count,
            }
            for status, count in rows
        ]

    # ---------------------------------------------------------
    # PLAN UTILIZATION
    # ---------------------------------------------------------

    def get_plan_utilization(self) -> list[dict]:
        plans = (
            self.db.query(ServicePlan)
            .order_by(ServicePlan.id)
            .all()
        )

        result = []

        for plan in plans:
            active_subscriptions = (
                self.db.query(
                    func.count(Subscription.id)
                )
                .filter(
                    Subscription.plan_id == plan.id,
                    Subscription.status
                    == SubscriptionStatus.ACTIVE,
                )
                .scalar()
                or 0
            )

            data_used = (
                self.db.query(
                    func.coalesce(
                        func.sum(Usage.data_used_mb),
                        0,
                    )
                )
                .join(
                    Subscription,
                    Subscription.id
                    == Usage.subscription_id,
                )
                .filter(
                    Subscription.plan_id == plan.id,
                    Subscription.status
                    == SubscriptionStatus.ACTIVE,
                    Usage.usage_type
                    == UsageType.DATA.value,
                    Usage.status.in_(
                        [
                            UsageStatus.RECORDED.value,
                            UsageStatus.PROCESSED.value,
                        ]
                    ),
                )
                .scalar()
            )

            data_used_decimal = Decimal(
                str(data_used or 0)
            )

            utilization_percentage = None

            if (
                plan.data_limit_mb is not None
                and plan.data_limit_mb > 0
            ):
                utilization_percentage = round(
                    (
                        float(data_used_decimal)
                        / (
                            plan.data_limit_mb
                            * max(active_subscriptions, 1)
                        )
                    )
                    * 100,
                    2,
                )

            result.append(
                {
                    "plan_id": plan.id,
                    "plan_code": plan.plan_code,
                    "plan_name": plan.plan_name,
                    "service_type": (
                        plan.service_type.value
                        if hasattr(
                            plan.service_type,
                            "value",
                        )
                        else plan.service_type
                    ),
                    "plan_status": (
                        plan.status.value
                        if hasattr(
                            plan.status,
                            "value",
                        )
                        else plan.status
                    ),
                    "active_subscriptions": (
                        active_subscriptions
                    ),
                    "data_limit_mb": plan.data_limit_mb,
                    "data_used_mb": data_used_decimal,
                    "utilization_percentage": (
                        utilization_percentage
                    ),
                }
            )

        return result