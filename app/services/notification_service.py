from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from app.models.user import User
from app.repositories.notification_repository import (
    NotificationRepository,
)
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)


class NotificationService:

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _validate_pagination(
        page: int,
        page_size: int,
    ) -> None:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1",
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

    @staticmethod
    def _get_user(
        db: Session,
        user_id: int,
    ) -> User:

        user = db.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user cannot receive notifications",
            )

        return user

    @staticmethod
    def create(
        db: Session,
        data: NotificationCreate,
    ) -> Notification:

        NotificationService._get_user(
            db,
            data.user_id,
        )

        if data.event_key:
            existing = (
                NotificationRepository.get_by_event_key(
                    db,
                    data.event_key,
                )
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Notification for this event already exists",
                )

        if (
            data.channel == NotificationChannel.IN_APP
            and data.expires_at
            and data.expires_at <= NotificationService._utc_now()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notification expiration must be in the future",
            )

        notification = Notification(
            user_id=data.user_id,
            notification_type=data.notification_type,
            channel=data.channel,
            priority=data.priority,
            status=NotificationStatus.PENDING,
            title=data.title,
            message=data.message,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            event_key=data.event_key,
            expires_at=data.expires_at,
        )

        if data.channel == NotificationChannel.IN_APP:
            notification.status = NotificationStatus.SENT
            notification.sent_at = NotificationService._utc_now()

        return NotificationRepository.create(
            db,
            notification,
        )

    @staticmethod
    def get(
        db: Session,
        notification_id: int,
    ) -> Notification:

        notification = NotificationRepository.get_by_id(
            db,
            notification_id,
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        return NotificationService._refresh_expiration(
            db,
            notification,
        )

    @staticmethod
    def _refresh_expiration(
        db: Session,
        notification: Notification,
    ) -> Notification:

        if (
            notification.expires_at
            and notification.expires_at <= NotificationService._utc_now()
            and not notification.is_read
            and notification.status != NotificationStatus.EXPIRED
        ):
            notification.status = NotificationStatus.EXPIRED

            NotificationRepository.update(
                db,
                notification,
            )

        return notification

    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: int,
    ) -> Notification:

        notification = NotificationService.get(
            db,
            notification_id,
        )

        if notification.status == NotificationStatus.EXPIRED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expired notification cannot be marked as read",
            )

        if notification.is_read:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notification is already marked as read",
            )

        now = NotificationService._utc_now()

        notification.is_read = True
        notification.read_at = now
        notification.status = NotificationStatus.READ

        return NotificationRepository.update(
            db,
            notification,
        )

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: int,
    ) -> int:

        NotificationService._get_user(
            db,
            user_id,
        )

        _, notifications = (
            NotificationRepository.mark_all_read(
                db,
                user_id,
            )
        )

        now = NotificationService._utc_now()

        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            notification.status = NotificationStatus.READ

        if notifications:
            db.flush()

        return len(notifications)

    @staticmethod
    def update(
        db: Session,
        notification_id: int,
        data: NotificationUpdate,
    ) -> Notification:

        notification = NotificationService.get(
            db,
            notification_id,
        )

        if notification.is_read:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Read notification cannot be updated",
            )

        if data.priority is not None:
            notification.priority = data.priority

        if data.expires_at is not None:
            if data.expires_at <= NotificationService._utc_now():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Expiration must be in the future",
                )

            notification.expires_at = data.expires_at

        if data.status is not None:
            if data.status == NotificationStatus.READ:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Use mark_as_read to mark a notification as read",
                )

            notification.status = data.status

        return NotificationRepository.update(
            db,
            notification,
        )

    @staticmethod
    def list(
        db: Session,
        *,
        user_id: int | None = None,
        notification_type: NotificationType | None = None,
        channel: NotificationChannel | None = None,
        priority: NotificationPriority | None = None,
        status: NotificationStatus | None = None,
        is_read: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:

        NotificationService._validate_pagination(
            page,
            page_size,
        )

        total = NotificationRepository.count(
            db,
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            priority=priority,
            status=status,
            is_read=is_read,
            search=search,
        )

        items = NotificationRepository.list(
            db,
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            priority=priority,
            status=status,
            is_read=is_read,
            search=search,
            page=page,
            page_size=page_size,
        )

        for item in items:
            NotificationService._refresh_expiration(
                db,
                item,
            )

        pages = ceil(total / page_size) if total else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }