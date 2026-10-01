from datetime import date

from sqlalchemy.orm import Session

from app.repositories.reports_repository import (
    ReportsRepository,
)


class ReportsService:

    @staticmethod
    def get_customer_summary(
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        repository = ReportsRepository(db)

        return repository.get_customer_summary(
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def get_usage_report(
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        subscription_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        repository = ReportsRepository(db)

        items, total_usage, total_records = (
            repository.get_usage_report(
                start_date=start_date,
                end_date=end_date,
                customer_id=customer_id,
                plan_id=plan_id,
                subscription_id=subscription_id,
                page=page,
                page_size=page_size,
            )
        )

        total_pages = (
            (total_records + page_size - 1)
            // page_size
            if total_records
            else 0
        )

        return {
            "items": items,
            "total_data_used_mb": total_usage,
            "total_records": total_records,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    def get_network_report(
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        tower_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        repository = ReportsRepository(db)

        return repository.get_network_report(
            start_date=start_date,
            end_date=end_date,
            tower_id=tower_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_support_report(
        db: Session,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        repository = ReportsRepository(db)

        return repository.get_support_report(
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_technician_report(
        db: Session,
        technician_id: int | None = None,
        status: str | None = None,
    ):
        repository = ReportsRepository(db)

        return repository.get_technician_report(
            technician_id=technician_id,
            status=status,
        )

    @staticmethod
    def get_overview(db: Session):
        repository = ReportsRepository(db)

        return repository.get_overview()