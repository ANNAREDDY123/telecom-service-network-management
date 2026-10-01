from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.sim_card import SIMCard, SIMStatus, SIMType


class SIMCardRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        sim_id: int,
    ) -> SIMCard | None:
        return self.db.scalar(
            select(SIMCard).where(
                SIMCard.id == sim_id
            )
        )

    def get_by_sim_number(
        self,
        sim_number: str,
    ) -> SIMCard | None:
        return self.db.scalar(
            select(SIMCard).where(
                func.lower(SIMCard.sim_number)
                == sim_number.lower()
            )
        )

    def get_active_customer_sim(
        self,
        customer_id: int,
    ) -> SIMCard | None:
        return self.db.scalar(
            select(SIMCard).where(
                SIMCard.customer_id == customer_id,
                SIMCard.status == SIMStatus.ACTIVE,
            )
        )

    def create(
        self,
        sim: SIMCard,
    ) -> SIMCard:
        self.db.add(sim)
        self.db.commit()
        self.db.refresh(sim)

        return sim

    def update(
        self,
        sim: SIMCard,
    ) -> SIMCard:
        self.db.add(sim)
        self.db.commit()
        self.db.refresh(sim)

        return sim

    def search(
        self,
        search: str | None = None,
        sim_type: SIMType | None = None,
        sim_status: SIMStatus | None = None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[SIMCard], int]:

        query = select(SIMCard)

        if search:
            pattern = f"%{search}%"

            query = query.where(
                or_(
                    SIMCard.sim_number.ilike(
                        pattern
                    ),
                )
            )

        if sim_type is not None:
            query = query.where(
                SIMCard.sim_type == sim_type
            )

        if sim_status is not None:
            query = query.where(
                SIMCard.status == sim_status
            )

        if customer_id is not None:
            query = query.where(
                SIMCard.customer_id == customer_id
            )

        if plan_id is not None:
            query = query.where(
                SIMCard.plan_id == plan_id
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        sims = list(
            self.db.scalars(
                query
                .order_by(SIMCard.id.desc())
                .offset(skip)
                .limit(limit)
            )
        )

        return sims, total