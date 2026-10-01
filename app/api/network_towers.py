from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.network_tower import (
    TowerStatus,
    TowerType,
)
from app.schemas.network_tower import (
    NetworkTowerCreate,
    NetworkTowerResponse,
    NetworkTowerStatusUpdate,
    NetworkTowerUpdate,
)
from app.services.network_tower_service import (
    NetworkTowerService,
)
from app.utils.dependencies import (
    get_current_user,
    require_roles,
)
from app.models.user import (
    User,
    UserRole,
)


router = APIRouter(
    prefix="/network-towers",
    tags=["Network Towers"],
)


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.NETWORK_ENGINEER,
]


@router.post(
    "",
    response_model=NetworkTowerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_network_tower(
    data: NetworkTowerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkTowerService(db)

    return service.create_tower(data)


@router.get(
    "",
)
def search_network_towers(
    tower_status: TowerStatus | None = Query(
        default=None,
        alias="status",
    ),
    tower_type: TowerType | None = None,
    city: str | None = None,
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
    service = NetworkTowerService(db)

    return service.search_towers(
        status=tower_status,
        tower_type=tower_type,
        city=city,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/active",
    response_model=list[NetworkTowerResponse],
)
def get_active_network_towers(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = NetworkTowerService(db)

    return service.get_active_towers()


@router.get(
    "/{tower_id}",
    response_model=NetworkTowerResponse,
)
def get_network_tower(
    tower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = NetworkTowerService(db)

    return service.get_tower(tower_id)


@router.put(
    "/{tower_id}",
    response_model=NetworkTowerResponse,
)
def update_network_tower(
    tower_id: int,
    data: NetworkTowerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkTowerService(db)

    return service.update_tower(
        tower_id,
        data,
    )


@router.patch(
    "/{tower_id}/status",
    response_model=NetworkTowerResponse,
)
def update_network_tower_status(
    tower_id: int,
    data: NetworkTowerStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkTowerService(db)

    return service.update_status(
        tower_id,
        data,
    )


@router.patch(
    "/{tower_id}/activate",
    response_model=NetworkTowerResponse,
)
def activate_network_tower(
    tower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkTowerService(db)

    return service.activate_tower(
        tower_id
    )


@router.patch(
    "/{tower_id}/deactivate",
    response_model=NetworkTowerResponse,
)
def deactivate_network_tower(
    tower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkTowerService(db)

    return service.deactivate_tower(
        tower_id
    )


@router.patch(
    "/{tower_id}/maintenance",
    response_model=NetworkTowerResponse,
)
def maintenance_network_tower(
    tower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = NetworkTowerService(db)

    return service.put_under_maintenance(
        tower_id
    )