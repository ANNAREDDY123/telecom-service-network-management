from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.field_technician import (
    FieldTechnician,
    TechnicianAvailability,
    TechnicianStatus,
)
from app.models.user import User, UserRole
from app.repositories.field_technician_repository import (
    FieldTechnicianRepository,
)
from app.schemas.field_technician import (
    FieldTechnicianCreate,
    FieldTechnicianUpdate,
    TechnicianAvailabilityUpdate,
    TechnicianStatusUpdate,
)


class FieldTechnicianService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = FieldTechnicianRepository(db)

    def create_technician(
        self,
        data: FieldTechnicianCreate,
    ) -> FieldTechnician:

        user = self.db.get(User, data.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.role != UserRole.FIELD_TECHNICIAN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "User must have Field Technician role"
                ),
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive",
            )

        existing_user = (
            self.repository.get_by_user_id(
                data.user_id
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Technician profile already exists "
                    "for this user"
                ),
            )

        existing_code = (
            self.repository.get_by_code(
                data.technician_code
            )
        )

        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Technician code already exists",
            )

        if (
            data.status == TechnicianStatus.INACTIVE
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "New technician cannot be created "
                    "with Inactive status"
                ),
            )

        technician = FieldTechnician(
            user_id=data.user_id,
            technician_code=data.technician_code,
            specialization=data.specialization,
            skills=data.skills,
            service_area=data.service_area,
            city=data.city,
            state=data.state,
            status=data.status,
            availability=data.availability,
            is_active=True,
            joined_date=data.joined_date,
            notes=data.notes,
        )

        try:
            return self.repository.create(
                technician
            )
        except Exception:
            self.db.rollback()
            raise

    def get_technician(
        self,
        technician_id: int,
    ) -> FieldTechnician:

        technician = self.repository.get_by_id(
            technician_id
        )

        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field technician not found",
            )

        return technician

    def update_technician(
        self,
        technician_id: int,
        data: FieldTechnicianUpdate,
    ) -> FieldTechnician:

        technician = self.get_technician(
            technician_id
        )

        if not technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Inactive technician cannot be updated"
                ),
            )

        updates = data.model_dump(
            exclude_unset=True
        )

        if "status" in updates:
            self._validate_status_transition(
                technician.status,
                updates["status"],
            )

        if (
            updates.get("status")
            == TechnicianStatus.INACTIVE
        ):
            technician.is_active = False
            technician.availability = (
                TechnicianAvailability.UNAVAILABLE
            )

        for field, value in updates.items():
            setattr(
                technician,
                field,
                value,
            )

        return self.repository.update(
            technician
        )

    def update_status(
        self,
        technician_id: int,
        data: TechnicianStatusUpdate,
    ) -> FieldTechnician:

        technician = self.get_technician(
            technician_id
        )

        self._validate_status_transition(
            technician.status,
            data.status,
        )

        technician.status = data.status

        if (
            data.status
            == TechnicianStatus.INACTIVE
        ):
            technician.is_active = False
            technician.availability = (
                TechnicianAvailability.UNAVAILABLE
            )
        else:
            technician.is_active = True

        return self.repository.update(
            technician
        )

    def update_availability(
        self,
        technician_id: int,
        data: TechnicianAvailabilityUpdate,
    ) -> FieldTechnician:

        technician = self.get_technician(
            technician_id
        )

        if not technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Inactive technician cannot "
                    "change availability"
                ),
            )

        if (
            technician.status
            == TechnicianStatus.ON_LEAVE
            and data.availability
            == TechnicianAvailability.AVAILABLE
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Technician on leave cannot "
                    "be marked available"
                ),
            )

        technician.availability = (
            data.availability
        )

        return self.repository.update(
            technician
        )

    def deactivate_technician(
        self,
        technician_id: int,
    ) -> FieldTechnician:

        technician = self.get_technician(
            technician_id
        )

        if not technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Technician is already inactive",
            )

        technician.is_active = False
        technician.status = (
            TechnicianStatus.INACTIVE
        )
        technician.availability = (
            TechnicianAvailability.UNAVAILABLE
        )

        return self.repository.update(
            technician
        )

    def activate_technician(
        self,
        technician_id: int,
    ) -> FieldTechnician:

        technician = self.get_technician(
            technician_id
        )

        if technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Technician is already active",
            )

        technician.is_active = True
        technician.status = (
            TechnicianStatus.AVAILABLE
        )
        technician.availability = (
            TechnicianAvailability.AVAILABLE
        )

        return self.repository.update(
            technician
        )

    def list_technicians(
        self,
        *,
        status_value: TechnicianStatus | None = None,
        availability: TechnicianAvailability | None = None,
        city: str | None = None,
        service_area: str | None = None,
        specialization: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ):

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be at least 1",
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100",
            )

        technicians, total = (
            self.repository.list_technicians(
                status=status_value,
                availability=availability,
                city=city,
                service_area=service_area,
                specialization=specialization,
                is_active=is_active,
                search=search,
                page=page,
                limit=limit,
            )
        )

        pages = ceil(total / limit) if total else 0

        return {
            "items": technicians,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    def get_available_technicians(
        self,
        *,
        city: str | None = None,
        service_area: str | None = None,
    ):
        return self.repository.get_available_technicians(
            city=city,
            service_area=service_area,
        )

    @staticmethod
    def _validate_status_transition(
        current_status,
        new_status,
    ):

        if current_status == new_status:
            return

        transitions = {
            TechnicianStatus.AVAILABLE: {
                TechnicianStatus.BUSY,
                TechnicianStatus.ON_LEAVE,
                TechnicianStatus.INACTIVE,
            },
            TechnicianStatus.BUSY: {
                TechnicianStatus.AVAILABLE,
                TechnicianStatus.ON_LEAVE,
                TechnicianStatus.INACTIVE,
            },
            TechnicianStatus.ON_LEAVE: {
                TechnicianStatus.AVAILABLE,
                TechnicianStatus.INACTIVE,
            },
            TechnicianStatus.INACTIVE: {
                TechnicianStatus.AVAILABLE,
            },
        }

        allowed = transitions.get(
            current_status,
            set(),
        )

        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid technician status transition: "
                    f"{current_status} -> {new_status}"
                ),
            )