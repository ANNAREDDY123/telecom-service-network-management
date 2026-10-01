from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.reports import (
    CustomerSummaryReport,
    NetworkReportResponse,
    ReportsOverviewResponse,
    SupportReportResponse,
    TechnicianReportResponse,
    UsageReportResponse,
)
from app.services.reports_service import (
    ReportsService,
)
from app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/reports",
    tags=["Advanced Reports"],
)


# ============================================================
# ROLE PERMISSIONS
# ============================================================

CUSTOMER_REPORT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
}

USAGE_REPORT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
}

NETWORK_REPORT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.NETWORK_ENGINEER,
}

SUPPORT_REPORT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.SUPPORT_AGENT,
}

TECHNICIAN_REPORT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
    UserRole.NETWORK_ENGINEER,
}

OVERVIEW_REPORT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.OPERATIONS_MANAGER,
}


def require_report_role(
    current_user: User,
    allowed_roles: set[UserRole],
):
    if current_user.role not in allowed_roles:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def validate_dates(
    start_date: date | None,
    end_date: date | None,
):
    if (
        start_date is not None
        and end_date is not None
        and end_date < start_date
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "end_date must be greater than "
                "or equal to start_date"
            ),
        )


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================


@router.get(
    "/overview",
    response_model=ReportsOverviewResponse,
)
def get_reports_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_report_role(
        current_user,
        OVERVIEW_REPORT_ROLES,
    )

    return ReportsService.get_overview(db)


# ============================================================
# CUSTOMER SUMMARY
# ============================================================


@router.get(
    "/customer-summary",
    response_model=CustomerSummaryReport,
)
def get_customer_summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_report_role(
        current_user,
        CUSTOMER_REPORT_ROLES,
    )

    validate_dates(
        start_date,
        end_date,
    )

    return ReportsService.get_customer_summary(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )


# ============================================================
# USAGE REPORT
# ============================================================


@router.get(
    "/usage",
    response_model=UsageReportResponse,
)
def get_usage_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    plan_id: int | None = Query(
        default=None,
        gt=0,
    ),
    subscription_id: int | None = Query(
        default=None,
        gt=0,
    ),
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
    require_report_role(
        current_user,
        USAGE_REPORT_ROLES,
    )

    validate_dates(
        start_date,
        end_date,
    )

    return ReportsService.get_usage_report(
        db=db,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        plan_id=plan_id,
        subscription_id=subscription_id,
        page=page,
        page_size=page_size,
    )


# ============================================================
# NETWORK REPORT
# ============================================================


@router.get(
    "/network",
    response_model=NetworkReportResponse,
)
def get_network_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    tower_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status: str | None = Query(default=None),
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
    require_report_role(
        current_user,
        NETWORK_REPORT_ROLES,
    )

    validate_dates(
        start_date,
        end_date,
    )

    return ReportsService.get_network_report(
        db=db,
        start_date=start_date,
        end_date=end_date,
        tower_id=tower_id,
        status=status,
        page=page,
        page_size=page_size,
    )


# ============================================================
# SUPPORT REPORT
# ============================================================


@router.get(
    "/support",
    response_model=SupportReportResponse,
)
def get_support_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status: str | None = Query(default=None),
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
    require_report_role(
        current_user,
        SUPPORT_REPORT_ROLES,
    )

    validate_dates(
        start_date,
        end_date,
    )

    return ReportsService.get_support_report(
        db=db,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        status=status,
        page=page,
        page_size=page_size,
    )


# ============================================================
# TECHNICIAN REPORT
# ============================================================


@router.get(
    "/technicians",
    response_model=TechnicianReportResponse,
)
def get_technician_report(
    technician_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_report_role(
        current_user,
        TECHNICIAN_REPORT_ROLES,
    )

    return ReportsService.get_technician_report(
        db=db,
        technician_id=technician_id,
        status=status,
    )