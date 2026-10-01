from datetime import date

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.network_tower import (
    NetworkTower,
    TowerStatus,
    TowerType,
)
from app.repositories.network_tower_repository import (
    NetworkTowerRepository,
)
from app.schemas.network_tower import (
    NetworkTowerCreate,
    NetworkTowerStatusUpdate,
    NetworkTowerUpdate,
)


class NetworkTowerService:

    def __init__(self, db: Session):
        self.repository = (
            NetworkTowerRepository(db)
        )

    def create_tower(
        self,
        data: NetworkTowerCreate,
    ) -> NetworkTower:

        existing = self.repository.get_by_code(
            data.tower_code
        )

        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=(
                    "Tower code already exists"
                ),
            )

        if (
            data.installation_date
            and data.installation_date
            > date.today()
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Installation date cannot "
                    "be in the future"
                ),
            )

        tower = NetworkTower(
            tower_code=data.tower_code,
            tower_name=data.tower_name,
            tower_type=data.tower_type,
            status=TowerStatus.PLANNED,
            latitude=data.latitude,
            longitude=data.longitude,
            address=data.address,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            coverage_radius_km=(
                data.coverage_radius_km
            ),
            capacity=data.capacity,
            installation_date=(
                data.installation_date
            ),
        )

        return self.repository.create(tower)

    def get_tower(
        self,
        tower_id: int,
    ) -> NetworkTower:

        tower = self.repository.get_by_id(
            tower_id
        )

        if not tower:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Network tower not found",
            )

        return tower

    def update_tower(
        self,
        tower_id: int,
        data: NetworkTowerUpdate,
    ) -> NetworkTower:

        tower = self.get_tower(tower_id)

        if tower.status == TowerStatus.DECOMMISSIONED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Decommissioned tower "
                    "cannot be updated"
                ),
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        if (
            "installation_date"
            in update_data
            and update_data["installation_date"]
            and update_data["installation_date"]
            > date.today()
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Installation date cannot "
                    "be in the future"
                ),
            )

        for field, value in update_data.items():
            setattr(tower, field, value)

        return self.repository.update(tower)

    def update_status(
        self,
        tower_id: int,
        data: NetworkTowerStatusUpdate,
    ) -> NetworkTower:

        tower = self.get_tower(tower_id)

        current_status = TowerStatus(
            tower.status
        )

        new_status = data.status

        transitions = {
            TowerStatus.PLANNED: {
                TowerStatus.ACTIVE,
                TowerStatus.INACTIVE,
                TowerStatus.DECOMMISSIONED,
            },
            TowerStatus.ACTIVE: {
                TowerStatus.MAINTENANCE,
                TowerStatus.INACTIVE,
            },
            TowerStatus.MAINTENANCE: {
                TowerStatus.ACTIVE,
                TowerStatus.INACTIVE,
            },
            TowerStatus.INACTIVE: {
                TowerStatus.ACTIVE,
                TowerStatus.DECOMMISSIONED,
            },
            TowerStatus.DECOMMISSIONED: set(),
        }

        allowed_statuses = transitions.get(
            current_status,
            set(),
        )

        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid tower status "
                    "transition from "
                    f"{current_status.value} "
                    f"to {new_status.value}"
                ),
            )

        if (
            new_status
            == TowerStatus.ACTIVE
        ):
            if (
                tower.installation_date
                and tower.installation_date
                > date.today()
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Tower cannot be activated "
                        "before installation date"
                    ),
                )

        if (
            new_status
            == TowerStatus.MAINTENANCE
        ):
            tower.last_maintenance_date = (
                date.today()
            )

        tower.status = new_status

        return self.repository.update(tower)

    def activate_tower(
        self,
        tower_id: int,
    ) -> NetworkTower:

        return self.update_status(
            tower_id,
            NetworkTowerStatusUpdate(
                status=TowerStatus.ACTIVE
            ),
        )

    def deactivate_tower(
        self,
        tower_id: int,
    ) -> NetworkTower:

        return self.update_status(
            tower_id,
            NetworkTowerStatusUpdate(
                status=TowerStatus.INACTIVE
            ),
        )

    def put_under_maintenance(
        self,
        tower_id: int,
    ) -> NetworkTower:

        return self.update_status(
            tower_id,
            NetworkTowerStatusUpdate(
                status=TowerStatus.MAINTENANCE
            ),
        )

    def search_towers(
        self,
        status: TowerStatus | None = None,
        tower_type: TowerType | None = None,
        city: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ):

        if skip < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Skip cannot be negative",
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Limit must be between "
                    "1 and 100"
                ),
            )

        towers = self.repository.search(
            status=status,
            tower_type=tower_type,
            city=city,
            search=search,
            skip=skip,
            limit=limit,
        )

        total = self.repository.count(
            status=status,
            tower_type=tower_type,
            city=city,
            search=search,
        )

        return {
            "items": towers,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    def get_active_towers(
        self,
    ) -> list[NetworkTower]:

        return self.repository.get_active_towers()