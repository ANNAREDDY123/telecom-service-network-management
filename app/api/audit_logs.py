from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.audit_log import (
    AuditLogListResponse,
    AuditLogResponse,
)
from app.services.audit_log_service import AuditLogService
from app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


AUDIT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
}


def require_audit_role(
    current_user: User,
):
    if current_user.role not in AUDIT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


@router.get(
    "/",
    response_model=AuditLogListResponse,
)
def list_audit_logs(
    user_id: int | None = Query(
        default=None,
        gt=0,
    ),
    action: str | None = Query(
        default=None,
        max_length=30,
    ),
    resource: str | None = Query(
        default=None,
        max_length=100,
    ),
    resource_id: int | None = Query(
        default=None,
        gt=0,
    ),
    method: str | None = Query(
        default=None,
        max_length=10,
    ),
    status_code: int | None = Query(
        default=None,
        ge=100,
        le=599,
    ),
    ip_address: str | None = Query(
        default=None,
        max_length=100,
    ),
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    require_audit_role(current_user)

    return AuditLogService.list_logs(
        db,
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        method=method,
        status_code=status_code,
        ip_address=ip_address,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    require_audit_role(current_user)

    audit_log = AuditLogService.get_by_id(
        db,
        audit_log_id,
    )

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return audit_log