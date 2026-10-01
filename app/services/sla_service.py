from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.sla_policy import SLAPolicy, SLAPriority, SLAStatus
from app.models.sla_tracking import SLATracking, SLATrackingStatus
from app.models.support_ticket import SupportTicket, TicketStatus
from app.repositories.sla_repository import SLARepository
from app.schemas.sla import (
    SLAPolicyCreate,
    SLAPolicyUpdate,
)


class SLAService:

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _validate_pagination(
        page: int,
        page_size: int,
    ) -> None:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1",
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _ensure_utc(
        value: datetime | None,
    ) -> datetime | None:
        """
        Normalize datetime values to UTC-aware datetimes.

        SQLite may return timezone-naive datetime values even when
        DateTime(timezone=True) is configured.
        """
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @staticmethod
    def _normalize_tracking_datetimes(
        tracking: SLATracking,
    ) -> SLATracking:
        """
        Normalize all SLA tracking datetime fields to
        timezone-aware UTC datetimes after SQLite persistence.
        """

        tracking.response_deadline = SLAService._ensure_utc(
            tracking.response_deadline
        )

        tracking.resolution_deadline = SLAService._ensure_utc(
            tracking.resolution_deadline
        )

        tracking.response_at = SLAService._ensure_utc(
            tracking.response_at
        )

        tracking.resolved_at = SLAService._ensure_utc(
            tracking.resolved_at
        )

        tracking.created_at = SLAService._ensure_utc(
            tracking.created_at
        )

        tracking.updated_at = SLAService._ensure_utc(
            tracking.updated_at
        )

        return tracking

    @staticmethod
    def _calculate_status(
        tracking: SLATracking,
        current_time: datetime | None = None,
    ) -> SLATrackingStatus:

        if tracking.resolved_at is not None:

            if (
                tracking.response_breached
                and tracking.resolution_breached
            ):
                return SLATrackingStatus.BOTH_BREACHED

            if tracking.resolution_breached:
                return SLATrackingStatus.RESOLUTION_BREACHED

            if tracking.response_breached:
                return SLATrackingStatus.RESPONSE_BREACHED

            return SLATrackingStatus.COMPLETED

        if (
            tracking.response_breached
            and tracking.resolution_breached
        ):
            return SLATrackingStatus.BOTH_BREACHED

        if tracking.resolution_breached:
            return SLATrackingStatus.RESOLUTION_BREACHED

        if tracking.response_breached:
            return SLATrackingStatus.RESPONSE_BREACHED

        return SLATrackingStatus.ON_TRACK

    # ============================================================
    # SLA POLICY MANAGEMENT
    # ============================================================

    @staticmethod
    def create_policy(
        db: Session,
        data: SLAPolicyCreate,
    ) -> SLAPolicy:

        existing = SLARepository.get_policy_by_code(
            db,
            data.sla_code,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SLA policy code already exists",
            )

        if (
            data.resolution_time_minutes
            <= data.response_time_minutes
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resolution time must be greater than response time",
            )

        policy = SLAPolicy(
            sla_code=data.sla_code.strip(),
            sla_name=data.sla_name.strip(),
            priority=data.priority,
            response_time_minutes=data.response_time_minutes,
            resolution_time_minutes=data.resolution_time_minutes,
            description=(
                data.description.strip()
                if data.description
                else None
            ),
            status=SLAStatus.ACTIVE,
            is_active=True,
        )

        return SLARepository.create_policy(
            db,
            policy,
        )

    @staticmethod
    def get_policy(
        db: Session,
        policy_id: int,
    ) -> SLAPolicy:

        policy = SLARepository.get_policy(
            db,
            policy_id,
        )

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA policy not found",
            )

        return policy

    @staticmethod
    def update_policy(
        db: Session,
        policy_id: int,
        data: SLAPolicyUpdate,
    ) -> SLAPolicy:

        policy = SLAService.get_policy(
            db,
            policy_id,
        )

        if not policy.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive SLA policy cannot be updated",
            )

        if data.sla_name is not None:
            policy.sla_name = data.sla_name.strip()

        if data.response_time_minutes is not None:
            policy.response_time_minutes = (
                data.response_time_minutes
            )

        if data.resolution_time_minutes is not None:
            policy.resolution_time_minutes = (
                data.resolution_time_minutes
            )

        if (
            policy.resolution_time_minutes
            <= policy.response_time_minutes
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resolution time must be greater than response time",
            )

        if data.description is not None:
            policy.description = (
                data.description.strip()
                if data.description.strip()
                else None
            )

        return SLARepository.update_policy(
            db,
            policy,
        )

    @staticmethod
    def update_policy_status(
        db: Session,
        policy_id: int,
        new_status: SLAStatus,
    ) -> SLAPolicy:

        policy = SLAService.get_policy(
            db,
            policy_id,
        )

        if policy.status == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SLA policy is already in the requested status",
            )

        if new_status == SLAStatus.INACTIVE:
            policy.status = SLAStatus.INACTIVE
            policy.is_active = False

        elif new_status == SLAStatus.ACTIVE:
            policy.status = SLAStatus.ACTIVE
            policy.is_active = True

        return SLARepository.update_policy(
            db,
            policy,
        )

    @staticmethod
    def list_policies(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        priority: SLAPriority | None = None,
        status: SLAStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[SLAPolicy], int]:

        SLAService._validate_pagination(
            page,
            page_size,
        )

        return SLARepository.list_policies(
            db=db,
            page=page,
            page_size=page_size,
            priority=priority,
            status=status,
            search=search,
        )

    # ============================================================
    # POLICY SELECTION
    # ============================================================

    @staticmethod
    def get_active_policy_for_priority(
        db: Session,
        priority,
    ) -> SLAPolicy:

        try:
            priority = SLAPriority(priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket priority",
            )

        items, _ = SLARepository.list_policies(
            db=db,
            page=1,
            page_size=1,
            priority=priority,
            status=SLAStatus.ACTIVE,
        )

        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active SLA policy found for this priority",
            )

        return items[0]

    # ============================================================
    # DEADLINE CALCULATION
    # ============================================================

    @staticmethod
    def calculate_deadlines(
        policy: SLAPolicy,
        start_time: datetime | None = None,
    ) -> tuple[datetime, datetime]:

        if not policy.is_active or policy.status != SLAStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot calculate deadlines using an inactive SLA policy",
            )

        if start_time is None:
            start_time = SLAService._utc_now()
        else:
            start_time = SLAService._ensure_utc(
                start_time
            )

        response_deadline = (
            start_time
            + timedelta(
                minutes=policy.response_time_minutes
            )
        )

        resolution_deadline = (
            start_time
            + timedelta(
                minutes=policy.resolution_time_minutes
            )
        )

        return (
            response_deadline,
            resolution_deadline,
        )

    # ============================================================
    # CREATE SLA TRACKING FOR TICKET
    # ============================================================

    @staticmethod
    def create_tracking_for_ticket(
        db: Session,
        ticket: SupportTicket,
        policy: SLAPolicy | None = None,
        start_time: datetime | None = None,
    ) -> SLATracking:

        existing = SLARepository.get_tracking_by_ticket(
            db,
            ticket.id,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SLA tracking already exists for this ticket",
            )

        if ticket.status in (
            TicketStatus.CLOSED,
            TicketStatus.CANCELLED,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SLA tracking cannot be created for a closed or cancelled ticket",
            )

        if policy is None:
            policy = SLAService.get_active_policy_for_priority(
                db,
                ticket.priority,
            )

        if start_time is None:
            start_time = SLAService._utc_now()
        else:
            start_time = SLAService._ensure_utc(
                start_time
            )

        response_deadline, resolution_deadline = (
            SLAService.calculate_deadlines(
                policy,
                start_time,
            )
        )

        tracking = SLATracking(
            ticket_id=ticket.id,
            sla_policy_id=policy.id,
            response_deadline=response_deadline,
            resolution_deadline=resolution_deadline,
            status=SLATrackingStatus.ON_TRACK,
            response_breached=False,
            resolution_breached=False,
        )

        tracking = SLARepository.create_tracking(
            db,
            tracking,
        )

        return SLAService._normalize_tracking_datetimes(
            tracking
        )

    # ============================================================
    # GET TRACKING
    # ============================================================

    @staticmethod
    def get_tracking(
        db: Session,
        tracking_id: int,
    ) -> SLATracking:

        tracking = SLARepository.get_tracking(
            db,
            tracking_id,
        )

        if not tracking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA tracking record not found",
            )

        return tracking

    @staticmethod
    def get_tracking_by_ticket(
        db: Session,
        ticket_id: int,
    ) -> SLATracking:

        tracking = SLARepository.get_tracking_by_ticket(
            db,
            ticket_id,
        )

        if not tracking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SLA tracking record not found for this ticket",
            )

        return tracking

    # ============================================================
    # BREACH DETECTION
    # ============================================================

    @staticmethod
    def detect_breaches(
        db: Session,
        tracking_id: int,
        current_time: datetime | None = None,
    ) -> SLATracking:

        tracking = SLAService.get_tracking(
            db,
            tracking_id,
        )

        if current_time is None:
            current_time = SLAService._utc_now()
        else:
            current_time = SLAService._ensure_utc(
                current_time
            )

        response_deadline = SLAService._ensure_utc(
            tracking.response_deadline
        )

        resolution_deadline = SLAService._ensure_utc(
            tracking.resolution_deadline
        )

        if tracking.response_at is None:
            if current_time > response_deadline:
                tracking.response_breached = True

        if tracking.resolved_at is None:
            if current_time > resolution_deadline:
                tracking.resolution_breached = True

        tracking.status = SLAService._calculate_status(
            tracking,
            current_time,
        )

        tracking = SLARepository.update_tracking(
            db,
            tracking,
        )

        return SLAService._normalize_tracking_datetimes(
            tracking
        )

    # ============================================================
    # RESPONSE TRACKING
    # ============================================================

    @staticmethod
    def record_response(
        db: Session,
        tracking_id: int,
        response_at: datetime | None = None,
    ) -> SLATracking:

        tracking = SLAService.get_tracking(
            db,
            tracking_id,
        )

        if tracking.response_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket response has already been recorded",
            )

        if tracking.resolved_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot record response after ticket resolution",
            )

        if response_at is None:
            response_at = SLAService._utc_now()
        else:
            response_at = SLAService._ensure_utc(
                response_at
            )

        response_deadline = SLAService._ensure_utc(
            tracking.response_deadline
        )

        tracking.response_at = response_at

        if response_at > response_deadline:
            tracking.response_breached = True

        tracking.status = SLAService._calculate_status(
            tracking
        )

        tracking = SLARepository.update_tracking(
            db,
            tracking,
        )

        return SLAService._normalize_tracking_datetimes(
            tracking
        )

    # ============================================================
    # RESOLUTION TRACKING
    # ============================================================

    @staticmethod
    def record_resolution(
        db: Session,
        tracking_id: int,
        resolved_at: datetime | None = None,
    ) -> SLATracking:

        tracking = SLAService.get_tracking(
            db,
            tracking_id,
        )

        if tracking.resolved_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket resolution has already been recorded",
            )

        if resolved_at is None:
            resolved_at = SLAService._utc_now()
        else:
            resolved_at = SLAService._ensure_utc(
                resolved_at
            )

        resolution_deadline = SLAService._ensure_utc(
            tracking.resolution_deadline
        )

        # Reconstruct the original SLA start time from the
        # resolution deadline and the policy duration.
        policy = SLARepository.get_policy(
            db,
            tracking.sla_policy_id,
        )

        if policy is not None:
            start_time = (
                resolution_deadline
                - timedelta(
                    minutes=policy.resolution_time_minutes
                )
            )

            start_time = SLAService._ensure_utc(
                start_time
            )

            if resolved_at < start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resolution time cannot be before SLA tracking creation time",
                )

        tracking.resolved_at = resolved_at

        if resolved_at > resolution_deadline:
            tracking.resolution_breached = True

        tracking.status = SLAService._calculate_status(
            tracking
        )

        tracking = SLARepository.update_tracking(
            db,
            tracking,
        )

        return SLAService._normalize_tracking_datetimes(
            tracking
        )

    # ============================================================
    # LIST TRACKING
    # ============================================================

    @staticmethod
    def list_tracking(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: SLATrackingStatus | None = None,
        policy_id: int | None = None,
        ticket_id: int | None = None,
    ) -> tuple[list[SLATracking], int]:

        SLAService._validate_pagination(
            page,
            page_size,
        )

        return SLARepository.list_tracking(
            db=db,
            page=page,
            page_size=page_size,
            status=status,
            policy_id=policy_id,
            ticket_id=ticket_id,
        )

    # ============================================================
    # BULK BREACH CHECK
    # ============================================================

    @staticmethod
    def check_all_active_breaches(
        db: Session,
        current_time: datetime | None = None,
    ) -> int:

        if current_time is None:
            current_time = SLAService._utc_now()
        else:
            current_time = SLAService._ensure_utc(
                current_time
            )

        items, _ = SLARepository.list_tracking(
            db=db,
            page=1,
            page_size=100,
        )

        updated_count = 0

        for tracking in items:

            if tracking.status == SLATrackingStatus.COMPLETED:
                continue

            SLAService.detect_breaches(
                db,
                tracking.id,
                current_time,
            )

            updated_count += 1

        return updated_count