from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.network_equipment import (
    EquipmentStatus,
    EquipmentType,
)
from app.models.user import (
    User,
    UserRole,
)
from app.schemas.network_equipment import (
    NetworkEquipmentCreate,
    NetworkEquipmentResponse,
    NetworkEquipmentStatusUpdate,
    NetworkEquipmentUpdate,
)
from app.services.network_equipment_service import (
    NetworkEquipmentService,
)
from app.utils.dependencies import (
    get_current_user,
    require_roles,
)


router = APIRouter(
    prefix="/network-equipment",
    tags=["Network Equipment"],
)


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.NETWORK_ENGINEER,
]


@router.post(
    "",
    response_model=NetworkEquipmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_network_equipment(
    data: NetworkEquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkEquipmentService(db)

    return service.create_equipment(data)


@router.get("")
def search_network_equipment(
    equipment_status: EquipmentStatus | None = Query(
        default=None,
        alias="status",
    ),
    equipment_type: EquipmentType | None = None,
    tower_id: int | None = Query(
        default=None,
        gt=0,
    ),
    search: str | None = None,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = NetworkEquipmentService(db)

    return service.search_equipment(
        status=equipment_status,
        equipment_type=equipment_type,
        tower_id=tower_id,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/tower/{tower_id}/active",
    response_model=list[NetworkEquipmentResponse],
)
def get_active_equipment_by_tower(
    tower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = NetworkEquipmentService(db)

    return service.get_active_equipment_by_tower(
        tower_id
    )


@router.get(
    "/{equipment_id}",
    response_model=NetworkEquipmentResponse,
)
def get_network_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = NetworkEquipmentService(db)

    return service.get_equipment(
        equipment_id
    )


@router.put(
    "/{equipment_id}",
    response_model=NetworkEquipmentResponse,
)
def update_network_equipment(
    equipment_id: int,
    data: NetworkEquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkEquipmentService(db)

    return service.update_equipment(
        equipment_id,
        data,
    )


@router.patch(
    "/{equipment_id}/status",
    response_model=NetworkEquipmentResponse,
)
def update_network_equipment_status(
    equipment_id: int,
    data: NetworkEquipmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkEquipmentService(db)

    return service.update_status(
        equipment_id,
        data,
    )


@router.patch(
    "/{equipment_id}/activate",
    response_model=NetworkEquipmentResponse,
)
def activate_network_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkEquipmentService(db)

    return service.activate_equipment(
        equipment_id
    )


@router.patch(
    "/{equipment_id}/deactivate",
    response_model=NetworkEquipmentResponse,
)
def deactivate_network_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkEquipmentService(db)

    return service.deactivate_equipment(
        equipment_id
    )


@router.patch(
    "/{equipment_id}/maintenance",
    response_model=NetworkEquipmentResponse,
)
def maintenance_network_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkEquipmentService(db)

    return service.put_under_maintenance(
        equipment_id
    )


@router.patch(
    "/{equipment_id}/failed",
    response_model=NetworkEquipmentResponse,
)
def fail_network_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkEquipmentService(db)

    return service.mark_failed(
        equipment_id
    )