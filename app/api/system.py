from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db


router = APIRouter(
    tags=["System"],
)


@router.get(
    "/health",
)
def health_check():

    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(
            timezone.utc
        ),
    }


@router.get(
    "/ready",
)
def readiness_check(
    db: Session = Depends(get_db),
):

    try:
        db.execute(
            text("SELECT 1")
        )

        database_status = "healthy"

    except Exception:

        database_status = "unhealthy"

        return {
            "status": "not_ready",
            "database": database_status,
            "application": settings.app_name,
            "version": settings.app_version,
        }

    return {
        "status": "ready",
        "database": database_status,
        "application": settings.app_name,
        "version": settings.app_version,
    }