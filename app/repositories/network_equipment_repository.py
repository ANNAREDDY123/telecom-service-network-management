from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.network_equipment import (
    EquipmentStatus,
    EquipmentType,
    NetworkEquipment,
)


class NetworkEquipmentRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        equipment_id: int,
    ) -> NetworkEquipment | None:
        return (
            self.db.query(NetworkEquipment)
            .filter(
                NetworkEquipment.id
                == equipment_id
            )
            .first()
        )

    def get_by_code(
        self,
        equipment_code: str,
    ) -> NetworkEquipment | None:
        return (
            self.db.query(NetworkEquipment)
            .filter(
                NetworkEquipment.equipment_code
                == equipment_code
            )
            .first()
        )

    def get_by_serial_number(
        self,
        serial_number: str,
    ) -> NetworkEquipment | None:
        return (
            self.db.query(NetworkEquipment)
            .filter(
                NetworkEquipment.serial_number
                == serial_number
            )
            .first()
        )

    def create(
        self,
        equipment: NetworkEquipment,
    ) -> NetworkEquipment:
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)

        return equipment

    def update(
        self,
        equipment: NetworkEquipment,
    ) -> NetworkEquipment:
        self.db.commit()
        self.db.refresh(equipment)

        return equipment

    def search(
        self,
        status: EquipmentStatus | None = None,
        equipment_type: EquipmentType | None = None,
        tower_id: int | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[NetworkEquipment]:

        query = self.db.query(
            NetworkEquipment
        )

        if status is not None:
            query = query.filter(
                NetworkEquipment.status
                == status
            )

        if equipment_type is not None:
            query = query.filter(
                NetworkEquipment.equipment_type
                == equipment_type
            )

        if tower_id is not None:
            query = query.filter(
                NetworkEquipment.tower_id
                == tower_id
            )

        if search:
            search_pattern = f"%{search}%"

            query = query.filter(
                or_(
                    NetworkEquipment.equipment_code.ilike(
                        search_pattern
                    ),
                    NetworkEquipment.serial_number.ilike(
                        search_pattern
                    ),
                    NetworkEquipment.equipment_name.ilike(
                        search_pattern
                    ),
                    NetworkEquipment.manufacturer.ilike(
                        search_pattern
                    ),
                )
            )

        return (
            query
            .order_by(
                NetworkEquipment.id.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(
        self,
        status: EquipmentStatus | None = None,
        equipment_type: EquipmentType | None = None,
        tower_id: int | None = None,
        search: str | None = None,
    ) -> int:

        query = self.db.query(
            NetworkEquipment
        )

        if status is not None:
            query = query.filter(
                NetworkEquipment.status
                == status
            )

        if equipment_type is not None:
            query = query.filter(
                NetworkEquipment.equipment_type
                == equipment_type
            )

        if tower_id is not None:
            query = query.filter(
                NetworkEquipment.tower_id
                == tower_id
            )

        if search:
            search_pattern = f"%{search}%"

            query = query.filter(
                or_(
                    NetworkEquipment.equipment_code.ilike(
                        search_pattern
                    ),
                    NetworkEquipment.serial_number.ilike(
                        search_pattern
                    ),
                    NetworkEquipment.equipment_name.ilike(
                        search_pattern
                    ),
                    NetworkEquipment.manufacturer.ilike(
                        search_pattern
                    ),
                )
            )

        return query.count()

    def get_active_by_tower(
        self,
        tower_id: int,
    ) -> list[NetworkEquipment]:

        return (
            self.db.query(NetworkEquipment)
            .filter(
                NetworkEquipment.tower_id
                == tower_id,
                NetworkEquipment.status
                == EquipmentStatus.ACTIVE,
            )
            .all()
        )