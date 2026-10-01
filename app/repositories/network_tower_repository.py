from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.network_tower import (
    NetworkTower,
    TowerStatus,
    TowerType,
)


class NetworkTowerRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        tower_id: int,
    ) -> NetworkTower | None:
        return (
            self.db.query(NetworkTower)
            .filter(NetworkTower.id == tower_id)
            .first()
        )

    def get_by_code(
        self,
        tower_code: str,
    ) -> NetworkTower | None:
        return (
            self.db.query(NetworkTower)
            .filter(
                NetworkTower.tower_code
                == tower_code
            )
            .first()
        )

    def create(
        self,
        tower: NetworkTower,
    ) -> NetworkTower:
        self.db.add(tower)
        self.db.commit()
        self.db.refresh(tower)

        return tower

    def update(
        self,
        tower: NetworkTower,
    ) -> NetworkTower:
        self.db.commit()
        self.db.refresh(tower)

        return tower

    def search(
        self,
        status: TowerStatus | None = None,
        tower_type: TowerType | None = None,
        city: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[NetworkTower]:

        query = self.db.query(NetworkTower)

        if status is not None:
            query = query.filter(
                NetworkTower.status == status
            )

        if tower_type is not None:
            query = query.filter(
                NetworkTower.tower_type
                == tower_type
            )

        if city:
            query = query.filter(
                NetworkTower.city.ilike(
                    f"%{city}%"
                )
            )

        if search:
            search_pattern = f"%{search}%"

            query = query.filter(
                or_(
                    NetworkTower.tower_code.ilike(
                        search_pattern
                    ),
                    NetworkTower.tower_name.ilike(
                        search_pattern
                    ),
                    NetworkTower.city.ilike(
                        search_pattern
                    ),
                )
            )

        return (
            query
            .order_by(NetworkTower.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(
        self,
        status: TowerStatus | None = None,
        tower_type: TowerType | None = None,
        city: str | None = None,
        search: str | None = None,
    ) -> int:

        query = self.db.query(NetworkTower)

        if status is not None:
            query = query.filter(
                NetworkTower.status == status
            )

        if tower_type is not None:
            query = query.filter(
                NetworkTower.tower_type
                == tower_type
            )

        if city:
            query = query.filter(
                NetworkTower.city.ilike(
                    f"%{city}%"
                )
            )

        if search:
            search_pattern = f"%{search}%"

            query = query.filter(
                or_(
                    NetworkTower.tower_code.ilike(
                        search_pattern
                    ),
                    NetworkTower.tower_name.ilike(
                        search_pattern
                    ),
                    NetworkTower.city.ilike(
                        search_pattern
                    ),
                )
            )

        return query.count()

    def get_active_towers(
        self,
    ) -> list[NetworkTower]:

        return (
            self.db.query(NetworkTower)
            .filter(
                NetworkTower.status
                == TowerStatus.ACTIVE
            )
            .all()
        )