from datetime import date

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.network_equipment import (
    EquipmentStatus,
    EquipmentType,
    NetworkEquipment,
)
from app.models.network_tower import (
    TowerStatus,
)
from app.repositories.network_equipment_repository import (
    NetworkEquipmentRepository,
)
from app.schemas.network_equipment import (
    NetworkEquipmentCreate,
    NetworkEquipmentStatusUpdate,
    NetworkEquipmentUpdate,
)


class NetworkEquipmentService:

    def __init__(self, db: Session):
        self.repository = (
            NetworkEquipmentRepository(db)
        )
        self.db = db

    def _get_tower(self, tower_id: int):
        from app.models.network_tower import (
            NetworkTower,
        )

        tower = (
            self.db.query(NetworkTower)
            .filter(
                NetworkTower.id == tower_id
            )
            .first()
        )

        if not tower:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Network tower not found",
            )

        return tower

    def _validate_tower_for_registration(
        self,
        tower_id: int,
    ):
        tower = self._get_tower(tower_id)

        if tower.status == TowerStatus.DECOMMISSIONED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Equipment cannot be assigned "
                    "to a decommissioned tower"
                ),
            )

        return tower

    def create_equipment(
        self,
        data: NetworkEquipmentCreate,
    ) -> NetworkEquipment:

        existing_code = (
            self.repository.get_by_code(
                data.equipment_code
            )
        )

        if existing_code:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=(
                    "Equipment code already exists"
                ),
            )

        existing_serial = (
            self.repository.get_by_serial_number(
                data.serial_number
            )
        )

        if existing_serial:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=(
                    "Equipment serial number "
                    "already exists"
                ),
            )

        self._validate_tower_for_registration(
            data.tower_id
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

        if (
            data.warranty_expiry_date
            and data.installation_date
            and data.warranty_expiry_date
            < data.installation_date
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Warranty expiry date cannot "
                    "be before installation date"
                ),
            )

        equipment = NetworkEquipment(
            equipment_code=data.equipment_code,
            serial_number=data.serial_number,
            equipment_name=data.equipment_name,
            equipment_type=data.equipment_type,
            manufacturer=data.manufacturer,
            model_number=data.model_number,
            status=EquipmentStatus.REGISTERED,
            tower_id=data.tower_id,
            capacity=data.capacity,
            installation_date=data.installation_date,
            warranty_expiry_date=(
                data.warranty_expiry_date
            ),
        )

        return self.repository.create(
            equipment
        )

    def get_equipment(
        self,
        equipment_id: int,
    ) -> NetworkEquipment:

        equipment = (
            self.repository.get_by_id(
                equipment_id
            )
        )

        if not equipment:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Network equipment not found",
            )

        return equipment

    def update_equipment(
        self,
        equipment_id: int,
        data: NetworkEquipmentUpdate,
    ) -> NetworkEquipment:

        equipment = self.get_equipment(
            equipment_id
        )

        if (
            equipment.status
            == EquipmentStatus.DECOMMISSIONED
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Decommissioned equipment "
                    "cannot be updated"
                ),
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No fields provided for update"
                ),
            )

        if "tower_id" in update_data:
            self._validate_tower_for_registration(
                update_data["tower_id"]
            )

        installation_date = update_data.get(
            "installation_date",
            equipment.installation_date,
        )

        warranty_expiry_date = update_data.get(
            "warranty_expiry_date",
            equipment.warranty_expiry_date,
        )

        if (
            installation_date
            and installation_date > date.today()
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Installation date cannot "
                    "be in the future"
                ),
            )

        if (
            warranty_expiry_date
            and installation_date
            and warranty_expiry_date
            < installation_date
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Warranty expiry date cannot "
                    "be before installation date"
                ),
            )

        for field, value in update_data.items():
            setattr(
                equipment,
                field,
                value,
            )

        return self.repository.update(
            equipment
        )

    def update_status(
        self,
        equipment_id: int,
        data: NetworkEquipmentStatusUpdate,
    ) -> NetworkEquipment:

        equipment = self.get_equipment(
            equipment_id
        )

        current_status = EquipmentStatus(
            equipment.status
        )

        new_status = data.status

        transitions = {
            EquipmentStatus.REGISTERED: {
                EquipmentStatus.ACTIVE,
                EquipmentStatus.INACTIVE,
                EquipmentStatus.DECOMMISSIONED,
            },
            EquipmentStatus.ACTIVE: {
                EquipmentStatus.MAINTENANCE,
                EquipmentStatus.INACTIVE,
                EquipmentStatus.FAILED,
            },
            EquipmentStatus.MAINTENANCE: {
                EquipmentStatus.ACTIVE,
                EquipmentStatus.INACTIVE,
                EquipmentStatus.FAILED,
            },
            EquipmentStatus.INACTIVE: {
                EquipmentStatus.ACTIVE,
                EquipmentStatus.DECOMMISSIONED,
            },
            EquipmentStatus.FAILED: {
                EquipmentStatus.MAINTENANCE,
                EquipmentStatus.ACTIVE,
                EquipmentStatus.INACTIVE,
                EquipmentStatus.DECOMMISSIONED,
            },
            EquipmentStatus.DECOMMISSIONED: set(),
        }

        allowed_statuses = transitions.get(
            current_status,
            set(),
        )

        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid equipment status "
                    "transition from "
                    f"{current_status.value} "
                    f"to {new_status.value}"
                ),
            )

        tower = self._get_tower(
            equipment.tower_id
        )

        if new_status == EquipmentStatus.ACTIVE:
            if (
                tower.status
                == TowerStatus.DECOMMISSIONED
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Equipment cannot be "
                        "activated on a "
                        "decommissioned tower"
                    ),
                )

            if (
                equipment.installation_date
                and equipment.installation_date
                > date.today()
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Equipment cannot be "
                        "activated before "
                        "installation date"
                    ),
                )

        if (
            new_status
            == EquipmentStatus.MAINTENANCE
        ):
            equipment.last_maintenance_date = (
                date.today()
            )

        equipment.status = new_status

        return self.repository.update(
            equipment
        )

    def activate_equipment(
        self,
        equipment_id: int,
    ) -> NetworkEquipment:

        return self.update_status(
            equipment_id,
            NetworkEquipmentStatusUpdate(
                status=EquipmentStatus.ACTIVE
            ),
        )

    def deactivate_equipment(
        self,
        equipment_id: int,
    ) -> NetworkEquipment:

        return self.update_status(
            equipment_id,
            NetworkEquipmentStatusUpdate(
                status=EquipmentStatus.INACTIVE
            ),
        )

    def put_under_maintenance(
        self,
        equipment_id: int,
    ) -> NetworkEquipment:

        return self.update_status(
            equipment_id,
            NetworkEquipmentStatusUpdate(
                status=EquipmentStatus.MAINTENANCE
            ),
        )

    def mark_failed(
        self,
        equipment_id: int,
    ) -> NetworkEquipment:

        return self.update_status(
            equipment_id,
            NetworkEquipmentStatusUpdate(
                status=EquipmentStatus.FAILED
            ),
        )

    def search_equipment(
        self,
        status: EquipmentStatus | None = None,
        equipment_type: EquipmentType | None = None,
        tower_id: int | None = None,
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

        result = self.repository.search(
            status=status,
            equipment_type=equipment_type,
            tower_id=tower_id,
            search=search,
            skip=skip,
            limit=limit,
        )

        total = self.repository.count(
            status=status,
            equipment_type=equipment_type,
            tower_id=tower_id,
            search=search,
        )

        return {
            "items": result,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    def get_active_equipment_by_tower(
        self,
        tower_id: int,
    ) -> list[NetworkEquipment]:

        self._get_tower(tower_id)

        return (
            self.repository.get_active_by_tower(
                tower_id
            )
        )
