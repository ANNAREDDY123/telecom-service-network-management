from datetime import date

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.usage import (
    Usage,
    UsageStatus,
    UsageType,
)


class UsageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        usage_id: int,
    ):
        return (
            self.db.query(Usage)
            .filter(
                Usage.id == usage_id
            )
            .first()
        )

    def get_by_reference_id(
        self,
        reference_id: str,
    ):
        return (
            self.db.query(Usage)
            .filter(
                Usage.reference_id
                == reference_id
            )
            .first()
        )

    def create(
        self,
        usage: Usage,
    ):
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)

        return usage

    def update(
        self,
        usage: Usage,
    ):
        self.db.commit()
        self.db.refresh(usage)

        return usage

    def search(
        self,
        customer_id: int | None = None,
        subscription_id: int | None = None,
        usage_type: UsageType | None = None,
        status: UsageStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ):
        query = self.db.query(Usage)

        if customer_id is not None:
            query = query.filter(
                Usage.customer_id
                == customer_id
            )

        if subscription_id is not None:
            query = query.filter(
                Usage.subscription_id
                == subscription_id
            )

        if usage_type is not None:
            query = query.filter(
                Usage.usage_type
                == usage_type
            )

        if status is not None:
            query = query.filter(
                Usage.status
                == status
            )

        if start_date is not None:
            query = query.filter(
                Usage.usage_date
                >= start_date
            )

        if end_date is not None:
            query = query.filter(
                Usage.usage_date
                <= end_date
            )

        if search:
            search_pattern = (
                f"%{search.strip()}%"
            )

            query = query.filter(
                or_(
                    Usage.reference_id.ilike(
                        search_pattern
                    ),
                    Usage.remarks.ilike(
                        search_pattern
                    ),
                )
            )

        return (
            query
            .order_by(
                Usage.usage_timestamp.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(
        self,
        customer_id: int | None = None,
        subscription_id: int | None = None,
        usage_type: UsageType | None = None,
        status: UsageStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        query = self.db.query(
            func.count(Usage.id)
        )

        if customer_id is not None:
            query = query.filter(
                Usage.customer_id
                == customer_id
            )

        if subscription_id is not None:
            query = query.filter(
                Usage.subscription_id
                == subscription_id
            )

        if usage_type is not None:
            query = query.filter(
                Usage.usage_type
                == usage_type
            )

        if status is not None:
            query = query.filter(
                Usage.status
                == status
            )

        if start_date is not None:
            query = query.filter(
                Usage.usage_date
                >= start_date
            )

        if end_date is not None:
            query = query.filter(
                Usage.usage_date
                <= end_date
            )

        return query.scalar() or 0

    def get_total_data_usage(
        self,
        subscription_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        query = self.db.query(
            func.coalesce(
                func.sum(
                    Usage.data_used_mb
                ),
                0,
            )
        ).filter(
            Usage.subscription_id
            == subscription_id,
            Usage.usage_type
            == UsageType.DATA,
            Usage.status
            != UsageStatus.REVERSED,
        )

        if start_date is not None:
            query = query.filter(
                Usage.usage_date
                >= start_date
            )

        if end_date is not None:
            query = query.filter(
                Usage.usage_date
                <= end_date
            )

        return query.scalar()

    def get_total_voice_usage(
        self,
        subscription_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        query = self.db.query(
            func.coalesce(
                func.sum(
                    Usage.voice_minutes
                ),
                0,
            )
        ).filter(
            Usage.subscription_id
            == subscription_id,
            Usage.usage_type
            == UsageType.VOICE,
            Usage.status
            != UsageStatus.REVERSED,
        )

        if start_date is not None:
            query = query.filter(
                Usage.usage_date
                >= start_date
            )

        if end_date is not None:
            query = query.filter(
                Usage.usage_date
                <= end_date
            )

        return query.scalar()

    def get_total_sms_usage(
        self,
        subscription_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        query = self.db.query(
            func.coalesce(
                func.sum(
                    Usage.sms_count
                ),
                0,
            )
        ).filter(
            Usage.subscription_id
            == subscription_id,
            Usage.usage_type
            == UsageType.SMS,
            Usage.status
            != UsageStatus.REVERSED,
        )

        if start_date is not None:
            query = query.filter(
                Usage.usage_date
                >= start_date
            )

        if end_date is not None:
            query = query.filter(
                Usage.usage_date
                <= end_date
            )

        return query.scalar()

    def get_usage_summary(
        self,
        subscription_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        data_used = (
            self.get_total_data_usage(
                subscription_id,
                start_date,
                end_date,
            )
        )

        voice_used = (
            self.get_total_voice_usage(
                subscription_id,
                start_date,
                end_date,
            )
        )

        sms_used = (
            self.get_total_sms_usage(
                subscription_id,
                start_date,
                end_date,
            )
        )

        return {
            "total_data_used_mb": data_used,
            "total_voice_minutes": voice_used,
            "total_sms_count": sms_used,
        }