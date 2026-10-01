from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.models.sim_card import SIMStatus, SIMType
from app.schemas.sim_card import (
    SIMCardCreate,
    SIMCardResponse,
    SIMCardUpdate,
    SIMReplacementCreate,
    SIMReplacementResponse,
    SIMStatusUpdate,
)
from app.services.sim_card_service import SIMCardService
from app.utils.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.db.database import get_db


router = APIRouter(
    prefix="/sim-cards",
    tags=["SIM Cards"],
)


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
]

SIM_VIEW_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
    UserRole.NETWORK_ENGINEER,
    UserRole.FIELD_TECHNICIAN,
    UserRole.CUSTOMER,
]


@router.post(
    "",
    response_model=SIMCardResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sim_card(
    data: SIMCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SIMCardService(db)

    return service.create_sim(data)


@router.get(
    "",
    response_model=list[SIMCardResponse],
)
def list_sim_cards(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    sim_type: SIMType | None = None,
    sim_status: SIMStatus | None = None,
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    plan_id: int | None = Query(
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
        require_roles(SIM_VIEW_ROLES)
    ),
):
    service = SIMCardService(db)

    sims, _ = service.search_sims(
        search=search,
        sim_type=sim_type,
        sim_status=sim_status,
        customer_id=customer_id,
        plan_id=plan_id,
        skip=skip,
        limit=limit,
    )

    return sims


@router.get(
    "/{sim_id}",
    response_model=SIMCardResponse,
)
def get_sim_card(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(SIM_VIEW_ROLES)
    ),
):
    service = SIMCardService(db)

    return service.get_sim(sim_id)


@router.put(
    "/{sim_id}",
    response_model=SIMCardResponse,
)
def update_sim_card(
    sim_id: int,
    data: SIMCardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SIMCardService(db)

    return service.update_sim(
        sim_id,
        data,
    )


@router.patch(
    "/{sim_id}/status",
    response_model=SIMCardResponse,
)
def update_sim_status(
    sim_id: int,
    data: SIMStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SIMCardService(db)

    return service.update_status(
        sim_id,
        data,
    )


@router.patch(
    "/{sim_id}/activate",
    response_model=SIMCardResponse,
)
def activate_sim_card(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SIMCardService(db)

    return service.activate_sim(sim_id)


@router.post(
    "/{sim_id}/replace",
    response_model=SIMReplacementResponse,
    status_code=status.HTTP_201_CREATED,
)
def replace_sim_card(
    sim_id: int,
    data: SIMReplacementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(MANAGEMENT_ROLES)
    ),
):
    service = SIMCardService(db)

    old_sim, new_sim = service.replace_sim(
        sim_id,
        data,
    )

    return SIMReplacementResponse(
        message="SIM card replaced successfully",
        old_sim=old_sim,
        new_sim=new_sim,
    )