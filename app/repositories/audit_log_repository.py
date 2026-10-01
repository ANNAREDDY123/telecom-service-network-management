from datetime import date, datetime, time, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id: int | None,
        action: str,
        resource: str,
        resource_id: int | None,
        method: str,
        endpoint: str,
        status_code: int,
        ip_address: str | None,
        user_agent: str | None,
        request_id: str | None,
        details: str | None,
    ) -> AuditLog:

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details,
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        return audit_log

    def get_by_id(
        self,
        audit_log_id: int,
    ) -> AuditLog | None:

        return (
            self.db.query(AuditLog)
            .filter(AuditLog.id == audit_log_id)
            .first()
        )

    def list_logs(
        self,
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

        query = self.db.query(AuditLog)

        if user_id is not None:
            query = query.filter(
                AuditLog.user_id == user_id
            )

        if action:
            query = query.filter(
                AuditLog.action == action
            )

        if resource:
            query = query.filter(
                AuditLog.resource == resource
            )

        if resource_id is not None:
            query = query.filter(
                AuditLog.resource_id == resource_id
            )

        if method:
            query = query.filter(
                AuditLog.method == method.upper()
            )

        if status_code is not None:
            query = query.filter(
                AuditLog.status_code == status_code
            )

        if ip_address:
            query = query.filter(
                AuditLog.ip_address == ip_address
            )

        if start_date is not None:
            start_datetime = datetime.combine(
                start_date,
                time.min,
            ).replace(tzinfo=timezone.utc)

            query = query.filter(
                AuditLog.created_at >= start_datetime
            )

        if end_date is not None:
            end_datetime = datetime.combine(
                end_date,
                time.max,
            ).replace(tzinfo=timezone.utc)

            query = query.filter(
                AuditLog.created_at <= end_datetime
            )

        total = query.with_entities(
            func.count(AuditLog.id)
        ).scalar() or 0

        offset = (page - 1) * page_size

        items = (
            query
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total