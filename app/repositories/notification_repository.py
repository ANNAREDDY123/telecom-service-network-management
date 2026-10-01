from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


class NotificationRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        notification_id: int,
    ) -> Notification | None:
        return db.scalar(
            select(Notification).where(
                Notification.id == notification_id
            )
        )

    @staticmethod
    def get_by_event_key(
        db: Session,
        event_key: str,
    ) -> Notification | None:
        return db.scalar(
            select(Notification).where(
                Notification.event_key == event_key
            )
        )

    @staticmethod
    def create(
        db: Session,
        notification: Notification,
    ) -> Notification:
        db.add(notification)
        db.flush()
        db.refresh(notification)

        return notification

    @staticmethod
    def update(
        db: Session,
        notification: Notification,
    ) -> Notification:
        db.add(notification)
        db.flush()
        db.refresh(notification)

        return notification

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
    ) -> list[Notification]:

        query = select(Notification)

        if user_id is not None:
            query = query.where(
                Notification.user_id == user_id
            )

        if notification_type is not None:
            query = query.where(
                Notification.notification_type
                == notification_type
            )

        if channel is not None:
            query = query.where(
                Notification.channel == channel
            )

        if priority is not None:
            query = query.where(
                Notification.priority == priority
            )

        if status is not None:
            query = query.where(
                Notification.status == status
            )

        if is_read is not None:
            query = query.where(
                Notification.is_read == is_read
            )

        if search:
            pattern = f"%{search.strip()}%"

            query = query.where(
                or_(
                    Notification.title.ilike(pattern),
                    Notification.message.ilike(pattern),
                )
            )

        query = query.order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )

        query = query.offset(
            (page - 1) * page_size
        ).limit(page_size)

        return list(db.scalars(query).all())

    @staticmethod
    def count(
        db: Session,
        *,
        user_id: int | None = None,
        notification_type: NotificationType | None = None,
        channel: NotificationChannel | None = None,
        priority: NotificationPriority | None = None,
        status: NotificationStatus | None = None,
        is_read: bool | None = None,
        search: str | None = None,
    ) -> int:

        query = select(
            func.count(Notification.id)
        )

        if user_id is not None:
            query = query.where(
                Notification.user_id == user_id
            )

        if notification_type is not None:
            query = query.where(
                Notification.notification_type
                == notification_type
            )

        if channel is not None:
            query = query.where(
                Notification.channel == channel
            )

        if priority is not None:
            query = query.where(
                Notification.priority == priority
            )

        if status is not None:
            query = query.where(
                Notification.status == status
            )

        if is_read is not None:
            query = query.where(
                Notification.is_read == is_read
            )

        if search:
            pattern = f"%{search.strip()}%"

            query = query.where(
                or_(
                    Notification.title.ilike(pattern),
                    Notification.message.ilike(pattern),
                )
            )

        return db.scalar(query) or 0

    @staticmethod
    def mark_all_read(
        db: Session,
        user_id: int,
    ) -> int:

        notifications = db.scalars(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        ).all()

        return len(notifications), notifications