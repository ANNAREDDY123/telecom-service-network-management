from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.network_outage import (
    NetworkOutage,
    OutageAffectedCustomer,
    OutageSeverity,
    OutageStatus,
    OutageType,
)


class NetworkOutageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        outage: NetworkOutage,
    ) -> NetworkOutage:
        self.db.add(outage)
        self.db.commit()
        self.db.refresh(outage)

        return outage

    def get_by_id(
        self,
        outage_id: int,
    ) -> NetworkOutage | None:
        return self.db.get(
            NetworkOutage,
            outage_id,
        )

    def get_by_number(
        self,
        outage_number: str,
    ) -> NetworkOutage | None:
        statement = select(
            NetworkOutage
        ).where(
            NetworkOutage.outage_number
            == outage_number
        )

        return self.db.scalar(statement)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        status: OutageStatus | None = None,
        severity: OutageSeverity | None = None,
        outage_type: OutageType | None = None,
        tower_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[NetworkOutage], int]:

        statement = select(NetworkOutage)

        count_statement = select(
            func.count(NetworkOutage.id)
        )

        if status is not None:
            statement = statement.where(
                NetworkOutage.status == status
            )

            count_statement = count_statement.where(
                NetworkOutage.status == status
            )

        if severity is not None:
            statement = statement.where(
                NetworkOutage.severity == severity
            )

            count_statement = count_statement.where(
                NetworkOutage.severity == severity
            )

        if outage_type is not None:
            statement = statement.where(
                NetworkOutage.outage_type
                == outage_type
            )

            count_statement = count_statement.where(
                NetworkOutage.outage_type
                == outage_type
            )

        if tower_id is not None:
            statement = statement.where(
                NetworkOutage.tower_id
                == tower_id
            )

            count_statement = count_statement.where(
                NetworkOutage.tower_id
                == tower_id
            )

        if search:
            pattern = f"%{search}%"

            search_filter = (
                NetworkOutage.outage_number.ilike(
                    pattern
                )
                | NetworkOutage.title.ilike(
                    pattern
                )
                | NetworkOutage.description.ilike(
                    pattern
                )
                | NetworkOutage.root_cause.ilike(
                    pattern
                )
            )

            statement = statement.where(
                search_filter
            )

            count_statement = count_statement.where(
                search_filter
            )

        total = (
            self.db.scalar(count_statement)
            or 0
        )

        offset = (
            (page - 1)
            * page_size
        )

        statement = (
            statement
            .order_by(
                NetworkOutage.start_time.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(
                statement
            ).all()
        )

        return items, total

    def update(
        self,
        outage: NetworkOutage,
    ) -> NetworkOutage:
        self.db.commit()
        self.db.refresh(outage)

        return outage

    def get_affected_customer(
        self,
        outage_id: int,
        customer_id: int,
    ) -> OutageAffectedCustomer | None:

        statement = select(
            OutageAffectedCustomer
        ).where(
            OutageAffectedCustomer.outage_id
            == outage_id,
            OutageAffectedCustomer.customer_id
            == customer_id,
        )

        return self.db.scalar(statement)

    def list_affected_customers(
        self,
        outage_id: int,
    ) -> list[OutageAffectedCustomer]:

        statement = (
            select(OutageAffectedCustomer)
            .where(
                OutageAffectedCustomer.outage_id
                == outage_id
            )
            .order_by(
                OutageAffectedCustomer.identified_at.asc()
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    def count_affected_customers(
        self,
        outage_id: int,
    ) -> int:

        statement = select(
            func.count(
                OutageAffectedCustomer.id
            )
        ).where(
            OutageAffectedCustomer.outage_id
            == outage_id
        )

        return (
            self.db.scalar(statement)
            or 0
        )

    def get_active_outages(
        self,
        tower_id: int | None = None,
    ) -> list[NetworkOutage]:

        active_statuses = [
            OutageStatus.REPORTED,
            OutageStatus.INVESTIGATING,
            OutageStatus.IDENTIFIED,
            OutageStatus.IN_PROGRESS,
        ]

        statement = select(
            NetworkOutage
        ).where(
            NetworkOutage.status.in_(
                active_statuses
            )
        )

        if tower_id is not None:
            statement = statement.where(
                NetworkOutage.tower_id
                == tower_id
            )

        statement = statement.order_by(
            NetworkOutage.start_time.desc()
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )