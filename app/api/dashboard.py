from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    DashboardOverviewResponse,
)
from app.services.dashboard_service import (
    DashboardService,
)
from app.utils.dependencies import (
    get_current_user,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Operations Dashboard"],
)


MANAGEMENT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
    UserRole.NETWORK_ENGINEER,
    UserRole.FIELD_TECHNICIAN,
}


def require_dashboard_access(
    current_user: User,
) -> None:
    if current_user.role not in MANAGEMENT_ROLES:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    require_dashboard_access(current_user)

    return DashboardService.get_overview(db)