from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.field_technician import (
    TechnicianAvailability,
    TechnicianStatus,
)
from app.models.user import User, UserRole
from app.schemas.field_technician import (
    FieldTechnicianCreate,
    FieldTechnicianListResponse,
    FieldTechnicianResponse,
    FieldTechnicianUpdate,
    TechnicianAvailabilityUpdate,
    TechnicianStatusUpdate,
)
from app.services.field_technician_service import (
    FieldTechnicianService,
)
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/field-technicians",
    tags=["Field Technicians"],
)


MANAGEMENT_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
)


@router.post(
    "/",
    response_model=FieldTechnicianResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_technician(
    data: FieldTechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = FieldTechnicianService(db)

    technician = service.create_technician(
        data
    )

    db.commit()

    return technician


@router.get(
    "/",
    response_model=FieldTechnicianListResponse,
)
def list_technicians(
    status_value: TechnicianStatus | None = Query(
        default=None,
        alias="status",
    ),
    availability: TechnicianAvailability | None = None,
    city: str | None = None,
    service_area: str | None = None,
    specialization: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = FieldTechnicianService(db)

    return service.list_technicians(
        status_value=status_value,
        availability=availability,
        city=city,
        service_area=service_area,
        specialization=specialization,
        is_active=is_active,
        search=search,
        page=page,
        limit=limit,
    )


@router.get(
    "/available",
    response_model=list[FieldTechnicianResponse],
)
def get_available_technicians(
    city: str | None = None,
    service_area: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = FieldTechnicianService(db)

    return service.get_available_technicians(
        city=city,
        service_area=service_area,
    )


@router.get(
    "/{technician_id}",
    response_model=FieldTechnicianResponse,
)
def get_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
        )
    ),
):
    service = FieldTechnicianService(db)

    return service.get_technician(
        technician_id
    )


@router.put(
    "/{technician_id}",
    response_model=FieldTechnicianResponse,
)
def update_technician(
    technician_id: int,
    data: FieldTechnicianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = FieldTechnicianService(db)

    technician = service.update_technician(
        technician_id,
        data,
    )

    db.commit()

    return technician


@router.patch(
    "/{technician_id}/status",
    response_model=FieldTechnicianResponse,
)
def update_status(
    technician_id: int,
    data: TechnicianStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = FieldTechnicianService(db)

    technician = service.update_status(
        technician_id,
        data,
    )

    db.commit()

    return technician


@router.patch(
    "/{technician_id}/availability",
    response_model=FieldTechnicianResponse,
)
def update_availability(
    technician_id: int,
    data: TechnicianAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            *MANAGEMENT_ROLES,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    service = FieldTechnicianService(db)

    technician = service.update_availability(
        technician_id,
        data,
    )

    db.commit()

    return technician


@router.patch(
    "/{technician_id}/deactivate",
    response_model=FieldTechnicianResponse,
)
def deactivate_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = FieldTechnicianService(db)

    technician = service.deactivate_technician(
        technician_id
    )

    db.commit()

    return technician


@router.patch(
    "/{technician_id}/activate",
    response_model=FieldTechnicianResponse,
)
def activate_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    service = FieldTechnicianService(db)

    technician = service.activate_technician(
        technician_id
    )

    db.commit()

    return technician