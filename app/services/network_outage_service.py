from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.network_outage import (
    NetworkOutage,
    OutageAffectedCustomer,
    OutageSeverity,
    OutageStatus,
    OutageType,
)
from app.models.network_tower import (
    NetworkTower,
    TowerStatus,
)
from app.repositories.network_outage_repository import (
    NetworkOutageRepository,
)
from app.schemas.network_outage import (
    AffectedCustomersCreate,
    OutageCreate,
    OutageRestore,
    OutageStatusUpdate,
    OutageUpdate,
)


class NetworkOutageService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NetworkOutageRepository(db)

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(
            timezone.utc
        ).replace(tzinfo=None)

    def _get_outage_or_404(
        self,
        outage_id: int,
    ) -> NetworkOutage:

        outage = self.repository.get_by_id(
            outage_id
        )

        if not outage:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Network outage not found.",
            )

        return outage

    def _get_tower_or_404(
        self,
        tower_id: int,
    ) -> NetworkTower:

        tower = self.db.get(
            NetworkTower,
            tower_id,
        )

        if not tower:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Network tower not found.",
            )

        return tower

    def _get_customer_or_404(
        self,
        customer_id: int,
    ) -> Customer:

        customer = self.db.get(
            Customer,
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Customer not found.",
            )

        return customer

    def create_outage(
        self,
        data: OutageCreate,
        created_by: int | None = None,
    ) -> NetworkOutage:

        existing = self.repository.get_by_number(
            data.outage_number
        )

        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Outage number already exists.",
            )

        tower = self._get_tower_or_404(
            data.tower_id
        )

        if (
            tower.status
            == TowerStatus.DECOMMISSIONED
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Cannot create an outage for "
                    "a decommissioned tower."
                ),
            )

        now = self._utc_now()

        if data.start_time > now:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Outage start time cannot "
                    "be in the future."
                ),
            )

        outage = NetworkOutage(
            outage_number=data.outage_number,
            title=data.title,
            description=data.description,
            outage_type=data.outage_type,
            severity=data.severity,
            status=OutageStatus.REPORTED,
            tower_id=data.tower_id,
            start_time=data.start_time,
            expected_restore_time=(
                data.expected_restore_time
            ),
            root_cause=data.root_cause,
            created_by=created_by,
            affected_customer_count=0,
        )

        return self.repository.create(
            outage
        )

    def update_outage(
        self,
        outage_id: int,
        data: OutageUpdate,
    ) -> NetworkOutage:

        outage = self._get_outage_or_404(
            outage_id
        )

        if outage.status in {
            OutageStatus.RESTORED,
            OutageStatus.CLOSED,
            OutageStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Completed or cancelled "
                    "outages cannot be updated."
                ),
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        expected_restore_time = update_data.get(
            "expected_restore_time"
        )

        if (
            expected_restore_time is not None
            and expected_restore_time
            < outage.start_time
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Expected restore time cannot "
                    "be before outage start time."
                ),
            )

        for field, value in update_data.items():
            setattr(
                outage,
                field,
                value,
            )

        return self.repository.update(
            outage
        )

    def update_status(
        self,
        outage_id: int,
        data: OutageStatusUpdate,
    ) -> NetworkOutage:

        outage = self._get_outage_or_404(
            outage_id
        )

        current = outage.status
        new_status = data.status

        if current == new_status:
            return outage

        allowed_transitions = {
            OutageStatus.REPORTED: {
                OutageStatus.INVESTIGATING,
                OutageStatus.CANCELLED,
            },
            OutageStatus.INVESTIGATING: {
                OutageStatus.IDENTIFIED,
                OutageStatus.IN_PROGRESS,
                OutageStatus.CANCELLED,
            },
            OutageStatus.IDENTIFIED: {
                OutageStatus.IN_PROGRESS,
                OutageStatus.CANCELLED,
            },
            OutageStatus.IN_PROGRESS: {
                OutageStatus.RESTORED,
                OutageStatus.CANCELLED,
            },
            OutageStatus.RESTORED: {
                OutageStatus.CLOSED,
            },
            OutageStatus.CLOSED: set(),
            OutageStatus.CANCELLED: set(),
        }

        if new_status not in allowed_transitions.get(
            current,
            set(),
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid outage status "
                    f"transition: "
                    f"{current.value} -> "
                    f"{new_status.value}."
                ),
            )

        if new_status == OutageStatus.RESTORED:
            outage.actual_restore_time = (
                self._utc_now()
            )

        outage.status = new_status

        return self.repository.update(
            outage
        )

    def restore_outage(
        self,
        outage_id: int,
        data: OutageRestore,
    ) -> NetworkOutage:

        outage = self._get_outage_or_404(
            outage_id
        )

        if outage.status not in {
            OutageStatus.IN_PROGRESS,
            OutageStatus.IDENTIFIED,
        }:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only identified or in-progress "
                    "outages can be restored."
                ),
            )

        restore_time = (
            data.actual_restore_time
            or self._utc_now()
        )

        if restore_time < outage.start_time:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Restore time cannot be "
                    "before outage start time."
                ),
            )

        outage.actual_restore_time = (
            restore_time
        )

        outage.resolution_notes = (
            data.resolution_notes
        )

        outage.status = OutageStatus.RESTORED

        affected_customers = (
            self.repository.list_affected_customers(
                outage_id
            )
        )

        for affected in affected_customers:
            if affected.resolved_at is None:
                affected.resolved_at = (
                    restore_time
                )

        return self.repository.update(
            outage
        )

    def close_outage(
        self,
        outage_id: int,
    ) -> NetworkOutage:

        outage = self._get_outage_or_404(
            outage_id
        )

        if outage.status != OutageStatus.RESTORED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only restored outages "
                    "can be closed."
                ),
            )

        outage.status = OutageStatus.CLOSED

        return self.repository.update(
            outage
        )

    def cancel_outage(
        self,
        outage_id: int,
    ) -> NetworkOutage:

        outage = self._get_outage_or_404(
            outage_id
        )

        if outage.status in {
            OutageStatus.RESTORED,
            OutageStatus.CLOSED,
            OutageStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "This outage cannot be cancelled."
                ),
            )

        outage.status = OutageStatus.CANCELLED

        return self.repository.update(
            outage
        )

    def identify_affected_customers(
        self,
        outage_id: int,
        data: AffectedCustomersCreate,
    ) -> list[OutageAffectedCustomer]:

        outage = self._get_outage_or_404(
            outage_id
        )

        if outage.status in {
            OutageStatus.RESTORED,
            OutageStatus.CLOSED,
            OutageStatus.CANCELLED,
        }:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Affected customers cannot "
                    "be added to a completed outage."
                ),
            )

        results: list[
            OutageAffectedCustomer
        ] = []

        for customer_id in data.customer_ids:

            customer = self._get_customer_or_404(
                customer_id
            )

            if not customer.is_active:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Customer {customer_id} "
                        "is inactive and cannot "
                        "be marked as affected."
                    ),
                )

            existing = (
                self.repository.get_affected_customer(
                    outage_id,
                    customer_id,
                )
            )

            if existing:
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail=(
                        f"Customer {customer_id} "
                        "is already marked as "
                        "affected by this outage."
                    ),
                )

            affected = OutageAffectedCustomer(
                outage_id=outage_id,
                customer_id=customer_id,
            )

            self.db.add(affected)

            results.append(affected)

        if outage.status == OutageStatus.INVESTIGATING:
            outage.status = (
                OutageStatus.IDENTIFIED
            )

        self.db.flush()

        outage.affected_customer_count = (
            self.repository.count_affected_customers(
                outage_id
            )
        )

        self.db.commit()

        for item in results:
            self.db.refresh(item)

        self.db.refresh(outage)

        return results

    def get_affected_customers(
        self,
        outage_id: int,
    ) -> list[OutageAffectedCustomer]:

        self._get_outage_or_404(
            outage_id
        )

        return (
            self.repository.list_affected_customers(
                outage_id
            )
        )

    def get_active_outages(
        self,
        tower_id: int | None = None,
    ) -> list[NetworkOutage]:

        return self.repository.get_active_outages(
            tower_id=tower_id
        )

    def get_outage_summary(
        self,
        outage_id: int,
    ) -> dict:

        outage = self._get_outage_or_404(
            outage_id
        )

        duration_minutes = None

        if outage.actual_restore_time:
            duration = (
                outage.actual_restore_time
                - outage.start_time
            )

            duration_minutes = int(
                duration.total_seconds()
                / 60
            )

        elif outage.status not in {
            OutageStatus.CLOSED,
            OutageStatus.CANCELLED,
        }:
            duration = (
                self._utc_now()
                - outage.start_time
            )

            duration_minutes = int(
                duration.total_seconds()
                / 60
            )

        return {
            "outage_id": outage.id,
            "outage_number": (
                outage.outage_number
            ),
            "status": outage.status,
            "severity": outage.severity,
            "affected_customer_count": (
                outage.affected_customer_count
            ),
            "start_time": outage.start_time,
            "expected_restore_time": (
                outage.expected_restore_time
            ),
            "actual_restore_time": (
                outage.actual_restore_time
            ),
            "duration_minutes": duration_minutes,
        }

    def list_outages(
        self,
        *,
        page: int,
        page_size: int,
        status: OutageStatus | None = None,
        severity: OutageSeverity | None = None,
        outage_type: OutageType | None = None,
        tower_id: int | None = None,
        search: str | None = None,
    ):

        return self.repository.list(
            page=page,
            page_size=page_size,
            status=status,
            severity=severity,
            outage_type=outage_type,
            tower_id=tower_id,
            search=search,
        )

    def get_outage(
        self,
        outage_id: int,
    ) -> NetworkOutage:

        return self._get_outage_or_404(
            outage_id
        )