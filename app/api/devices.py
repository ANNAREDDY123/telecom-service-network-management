from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.device import DeviceStatus, DeviceType
from app.models.user import User, UserRole
from app.schemas.device import (
    DeviceCreate,
    DeviceReplacementCreate,
    DeviceReplacementResponse,
    DeviceResponse,
    DeviceStatusUpdate,
    DeviceUpdate,
)
from app.services.device_service import DeviceService
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
]

DEVICE_VIEW_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
    UserRole.NETWORK_ENGINEER,
    UserRole.FIELD_TECHNICIAN,
    UserRole.CUSTOMER,
]


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = DeviceService(db)

    return service.create_device(data)


@router.get(
    "",
    response_model=list[DeviceResponse],
)
def list_devices(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    device_type: DeviceType | None = None,
    device_status: DeviceStatus | None = None,
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    sim_id: int | None = Query(
        default=None,
        gt=0,
    ),
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
        require_roles(DEVICE_VIEW_ROLES)
    ),
):
    service = DeviceService(db)

    devices, _ = service.search_devices(
        search=search,
        device_type=device_type,
        device_status=device_status,
        customer_id=customer_id,
        sim_id=sim_id,
        skip=skip,
        limit=limit,
    )

    return devices


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(DEVICE_VIEW_ROLES)
    ),
):
    service = DeviceService(db)

    return service.get_device(device_id)


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
)
def update_device(
    device_id: int,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = DeviceService(db)

    return service.update_device(
        device_id,
        data,
    )


@router.patch(
    "/{device_id}/status",
    response_model=DeviceResponse,
)
def update_device_status(
    device_id: int,
    data: DeviceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = DeviceService(db)

    return service.update_status(
        device_id,
        data,
    )


@router.patch(
    "/{device_id}/activate",
    response_model=DeviceResponse,
)
def activate_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = DeviceService(db)

    return service.activate_device(device_id)


@router.post(
    "/{device_id}/replace",
    response_model=DeviceReplacementResponse,
    status_code=status.HTTP_201_CREATED,
)
def replace_device(
    device_id: int,
    data: DeviceReplacementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = DeviceService(db)

    old_device, new_device = service.replace_device(
        device_id,
        data,
    )

    return DeviceReplacementResponse(
        message="Device replaced successfully",
        old_device=old_device,
        new_device=new_device,
    )