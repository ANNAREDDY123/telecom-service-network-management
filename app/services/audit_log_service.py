from datetime import date
from math import ceil

from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import (
    AuditLogRepository,
)
from app.schemas.audit_log import AuditLogCreate


class AuditLogService:

    @staticmethod
    def create(
        db: Session,
        data: AuditLogCreate,
    ):

        repository = AuditLogRepository(db)

        return repository.create(
            user_id=data.user_id,
            action=data.action,
            resource=data.resource,
            resource_id=data.resource_id,
            method=data.method.upper(),
            endpoint=data.endpoint,
            status_code=data.status_code,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            request_id=data.request_id,
            details=data.details,
        )

    @staticmethod
    def get_by_id(
        db: Session,
        audit_log_id: int,
    ):

        repository = AuditLogRepository(db)

        return repository.get_by_id(
            audit_log_id
        )

    @staticmethod
    def list_logs(
        db: Session,
        *,
        user_id: int | None = None,
        action: str | None = None,
        resource: str | None = None,
        resource_id: int | None = None,
        method: str | None = None,
        status_code: int | None = None,
        ip_address: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ):

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "end_date must be greater than or equal "
                    "to start_date"
                ),
            )

        repository = AuditLogRepository(db)

        items, total = repository.list_logs(
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

        total_pages = (
            ceil(total / page_size)
            if total
            else 0
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }