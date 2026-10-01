from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.field_technician import (
    FieldTechnician,
    TechnicianAvailability,
    TechnicianStatus,
)


class FieldTechnicianRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        technician_id: int,
    ) -> FieldTechnician | None:
        return self.db.get(
            FieldTechnician,
            technician_id,
        )

    def get_by_user_id(
        self,
        user_id: int,
    ) -> FieldTechnician | None:
        statement = select(FieldTechnician).where(
            FieldTechnician.user_id == user_id
        )

        return self.db.scalar(statement)

    def get_by_code(
        self,
        technician_code: str,
    ) -> FieldTechnician | None:
        statement = select(FieldTechnician).where(
            FieldTechnician.technician_code
            == technician_code
        )

        return self.db.scalar(statement)

    def create(
        self,
        technician: FieldTechnician,
    ) -> FieldTechnician:
        self.db.add(technician)
        self.db.flush()
        self.db.refresh(technician)

        return technician

    def update(
        self,
        technician: FieldTechnician,
    ) -> FieldTechnician:
        self.db.flush()
        self.db.refresh(technician)

        return technician

    def list_technicians(
        self,
        *,
        status: TechnicianStatus | None = None,
        availability: TechnicianAvailability | None = None,
        city: str | None = None,
        service_area: str | None = None,
        specialization: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[FieldTechnician], int]:

        statement = select(FieldTechnician)
        count_statement = select(
            func.count(FieldTechnician.id)
        )

        conditions = []

        if status is not None:
            conditions.append(
                FieldTechnician.status == status
            )

        if availability is not None:
            conditions.append(
                FieldTechnician.availability
                == availability
            )

        if city:
            conditions.append(
                FieldTechnician.city.ilike(
                    f"%{city}%"
                )
            )

        if service_area:
            conditions.append(
                FieldTechnician.service_area.ilike(
                    f"%{service_area}%"
                )
            )

        if specialization:
            conditions.append(
                FieldTechnician.specialization.ilike(
                    f"%{specialization}%"
                )
            )

        if is_active is not None:
            conditions.append(
                FieldTechnician.is_active
                == is_active
            )

        if search:
            search_value = f"%{search}%"

            conditions.append(
                or_(
                    FieldTechnician.technician_code.ilike(
                        search_value
                    ),
                    FieldTechnician.specialization.ilike(
                        search_value
                    ),
                    FieldTechnician.service_area.ilike(
                        search_value
                    ),
                    FieldTechnician.city.ilike(
                        search_value
                    ),
                    FieldTechnician.state.ilike(
                        search_value
                    ),
                    FieldTechnician.skills.ilike(
                        search_value
                    ),
                )
            )

        if conditions:
            statement = statement.where(*conditions)
            count_statement = count_statement.where(
                *conditions
            )

        total = self.db.scalar(
            count_statement
        ) or 0

        statement = (
            statement
            .order_by(FieldTechnician.id)
            .offset((page - 1) * limit)
            .limit(limit)
        )

        technicians = list(
            self.db.scalars(statement).all()
        )

        return technicians, total

    def get_available_technicians(
        self,
        *,
        city: str | None = None,
        service_area: str | None = None,
    ) -> list[FieldTechnician]:

        statement = select(
            FieldTechnician
        ).where(
            FieldTechnician.is_active.is_(True),
            FieldTechnician.status
            == TechnicianStatus.AVAILABLE,
            FieldTechnician.availability
            == TechnicianAvailability.AVAILABLE,
        )

        if city:
            statement = statement.where(
                FieldTechnician.city.ilike(
                    f"%{city}%"
                )
            )

        if service_area:
            statement = statement.where(
                FieldTechnician.service_area.ilike(
                    f"%{service_area}%"
                )
            )

        statement = statement.order_by(
            FieldTechnician.id
        )

        return list(
            self.db.scalars(statement).all()
        )