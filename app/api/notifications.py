from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from app.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationReadResponse,
    NotificationResponse,
    NotificationUpdate,
)
from app.services.notification_service import (
    NotificationService,
)
from app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.create(
        db,
        data,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = NotificationService.get(
        db,
        notification_id,
    )

    if notification.user_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own notifications",
        )

    return notification


@router.get(
    "",
    response_model=NotificationListResponse,
)
def list_notifications(
    notification_type: NotificationType | None = None,
    channel: NotificationChannel | None = None,
    priority: NotificationPriority | None = None,
    notification_status: NotificationStatus | None = Query(
        default=None,
        alias="status",
    ),
    is_read: bool | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.list(
        db,
        user_id=current_user.id,
        notification_type=notification_type,
        channel=channel,
        priority=priority,
        status=notification_status,
        is_read=is_read,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def update_notification(
    notification_id: int,
    data: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = NotificationService.get(
        db,
        notification_id,
    )

    if notification.user_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own notifications",
        )

    return NotificationService.update(
        db,
        notification_id,
        data,
    )


@router.post(
    "/{notification_id}/read",
    response_model=NotificationReadResponse,
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = NotificationService.get(
        db,
        notification_id,
    )

    if notification.user_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own notifications",
        )

    notification = NotificationService.mark_as_read(
        db,
        notification_id,
    )

    return {
        "id": notification.id,
        "is_read": notification.is_read,
        "read_at": notification.read_at,
    }


@router.post(
    "/read-all",
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = NotificationService.mark_all_as_read(
        db,
        current_user.id,
    )

    return {
        "message": "All notifications marked as read",
        "updated_count": count,
    }