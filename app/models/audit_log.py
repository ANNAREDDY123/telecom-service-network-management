from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    resource_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    endpoint: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_audit_logs_user_created",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_audit_logs_resource_created",
            "resource",
            "created_at",
        ),
        Index(
            "ix_audit_logs_action_created",
            "action",
            "created_at",
        ),
    )