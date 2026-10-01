from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from app.models.user import User, UserRole
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)
from app.services.notification_service import (
    NotificationService,
)


_counter = 0


def unique_value(prefix: str) -> str:
    global _counter
    _counter += 1
    return f"{prefix}-{_counter}"


def create_user(
    db_session,
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
):
    user = User(
        full_name=f"Notification User {_counter + 1}",
        email=f"{unique_value('notification')}@example.com",
        phone=f"9{_counter + 100000000:09d}",
        hashed_password="hashed-password",
        role=role,
        is_active=is_active,
        is_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    return user


def create_notification(
    db_session,
    user_id: int,
    *,
    notification_type: NotificationType = NotificationType.GENERAL,
    channel: NotificationChannel = NotificationChannel.IN_APP,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    title: str = "Test Notification",
    message: str = "This is a test notification.",
    event_key: str | None = None,
):
    data = NotificationCreate(
        user_id=user_id,
        notification_type=notification_type,
        channel=channel,
        priority=priority,
        title=title,
        message=message,
        event_key=event_key,
    )

    return NotificationService.create(
        db_session,
        data,
    )


# -------------------------------------------------------------------
# Creation
# -------------------------------------------------------------------


def test_create_in_app_notification(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
    )

    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.notification_type == NotificationType.GENERAL
    assert notification.channel == NotificationChannel.IN_APP
    assert notification.status == NotificationStatus.SENT
    assert notification.is_read is False
    assert notification.sent_at is not None


def test_create_notification_with_priority(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
        priority=NotificationPriority.CRITICAL,
    )

    assert notification.priority == NotificationPriority.CRITICAL


def test_create_notification_with_reference(db_session):
    user = create_user(db_session)

    data = NotificationCreate(
        user_id=user.id,
        notification_type=NotificationType.TICKET_CREATED,
        channel=NotificationChannel.IN_APP,
        priority=NotificationPriority.HIGH,
        title="Ticket Created",
        message="Your support ticket was created.",
        reference_type="SupportTicket",
        reference_id=100,
    )

    notification = NotificationService.create(
        db_session,
        data,
    )

    assert notification.reference_type == "SupportTicket"
    assert notification.reference_id == 100


def test_missing_user_rejected(db_session):
    data = NotificationCreate(
        user_id=999999,
        notification_type=NotificationType.GENERAL,
        title="Test",
        message="Test message",
    )

    with pytest.raises(HTTPException) as exc:
        NotificationService.create(
            db_session,
            data,
        )

    assert exc.value.status_code == 404


def test_inactive_user_rejected(db_session):
    user = create_user(
        db_session,
        is_active=False,
    )

    data = NotificationCreate(
        user_id=user.id,
        notification_type=NotificationType.GENERAL,
        title="Test",
        message="Test message",
    )

    with pytest.raises(HTTPException) as exc:
        NotificationService.create(
            db_session,
            data,
        )

    assert exc.value.status_code == 400


# -------------------------------------------------------------------
# Event key / duplicate protection
# -------------------------------------------------------------------


def test_duplicate_event_key_rejected(db_session):
    user = create_user(db_session)

    create_notification(
        db_session,
        user.id,
        event_key="ticket-created-100",
    )

    data = NotificationCreate(
        user_id=user.id,
        notification_type=NotificationType.TICKET_CREATED,
        title="Duplicate",
        message="Duplicate event",
        event_key="ticket-created-100",
    )

    with pytest.raises(HTTPException) as exc:
        NotificationService.create(
            db_session,
            data,
        )

    assert exc.value.status_code == 409


def test_different_event_keys_allowed(db_session):
    user = create_user(db_session)

    first = create_notification(
        db_session,
        user.id,
        event_key="event-1",
    )

    second = create_notification(
        db_session,
        user.id,
        event_key="event-2",
    )

    assert first.id != second.id


# -------------------------------------------------------------------
# Notification channels
# -------------------------------------------------------------------


def test_email_notification_starts_pending(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
        channel=NotificationChannel.EMAIL,
    )

    assert notification.channel == NotificationChannel.EMAIL
    assert notification.status == NotificationStatus.PENDING
    assert notification.sent_at is None


def test_sms_notification_starts_pending(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
        channel=NotificationChannel.SMS,
    )

    assert notification.channel == NotificationChannel.SMS
    assert notification.status == NotificationStatus.PENDING


# -------------------------------------------------------------------
# Get notification
# -------------------------------------------------------------------


def test_get_notification(db_session):
    user = create_user(db_session)

    created = create_notification(
        db_session,
        user.id,
    )

    notification = NotificationService.get(
        db_session,
        created.id,
    )

    assert notification.id == created.id
    assert notification.user_id == user.id


def test_missing_notification_returns_404(db_session):
    with pytest.raises(HTTPException) as exc:
        NotificationService.get(
            db_session,
            999999,
        )

    assert exc.value.status_code == 404


# -------------------------------------------------------------------
# Mark as read
# -------------------------------------------------------------------


def test_mark_notification_as_read(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
    )

    updated = NotificationService.mark_as_read(
        db_session,
        notification.id,
    )

    assert updated.is_read is True
    assert updated.status == NotificationStatus.READ
    assert updated.read_at is not None


def test_duplicate_mark_as_read_rejected(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
    )

    NotificationService.mark_as_read(
        db_session,
        notification.id,
    )

    with pytest.raises(HTTPException) as exc:
        NotificationService.mark_as_read(
            db_session,
            notification.id,
        )

    assert exc.value.status_code == 400


# -------------------------------------------------------------------
# Mark all as read
# -------------------------------------------------------------------


def test_mark_all_notifications_as_read(db_session):
    user = create_user(db_session)

    create_notification(
        db_session,
        user.id,
        event_key="read-all-1",
    )

    create_notification(
        db_session,
        user.id,
        event_key="read-all-2",
    )

    count = NotificationService.mark_all_as_read(
        db_session,
        user.id,
    )

    assert count == 2


def test_mark_all_notifications_only_affects_target_user(
    db_session,
):
    user_one = create_user(db_session)
    user_two = create_user(db_session)

    first = create_notification(
        db_session,
        user_one.id,
        event_key="target-user-1",
    )

    second = create_notification(
        db_session,
        user_two.id,
        event_key="target-user-2",
    )

    count = NotificationService.mark_all_as_read(
        db_session,
        user_one.id,
    )

    assert count == 1

    refreshed_first = NotificationService.get(
        db_session,
        first.id,
    )

    refreshed_second = NotificationService.get(
        db_session,
        second.id,
    )

    assert refreshed_first.is_read is True
    assert refreshed_second.is_read is False


# -------------------------------------------------------------------
# Expiration
# -------------------------------------------------------------------


def test_expired_notification_becomes_expired(db_session):
    user = create_user(db_session)

    data = NotificationCreate(
        user_id=user.id,
        notification_type=NotificationType.GENERAL,
        title="Expired",
        message="Expired notification",
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=1),
    )

    notification = NotificationService.create(
        db_session,
        data,
    )

    notification.expires_at = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    )

    db_session.flush()

    refreshed = NotificationService.get(
        db_session,
        notification.id,
    )

    assert refreshed.status == NotificationStatus.EXPIRED


def test_expired_notification_cannot_be_marked_read(db_session):
    user = create_user(db_session)

    data = NotificationCreate(
        user_id=user.id,
        notification_type=NotificationType.GENERAL,
        title="Expired",
        message="Expired notification",
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=1),
    )

    notification = NotificationService.create(
        db_session,
        data,
    )

    notification.expires_at = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    )

    db_session.flush()

    with pytest.raises(HTTPException) as exc:
        NotificationService.mark_as_read(
            db_session,
            notification.id,
        )

    assert exc.value.status_code == 400


# -------------------------------------------------------------------
# Update
# -------------------------------------------------------------------


def test_update_notification_priority(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
    )

    updated = NotificationService.update(
        db_session,
        notification.id,
        NotificationUpdate(
            priority=NotificationPriority.HIGH,
        ),
    )

    assert updated.priority == NotificationPriority.HIGH


def test_update_notification_expiration(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
    )

    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=2
    )

    updated = NotificationService.update(
        db_session,
        notification.id,
        NotificationUpdate(
            expires_at=expires_at,
        ),
    )

    assert updated.expires_at is not None


def test_read_notification_cannot_be_updated(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
    )

    NotificationService.mark_as_read(
        db_session,
        notification.id,
    )

    with pytest.raises(HTTPException) as exc:
        NotificationService.update(
            db_session,
            notification.id,
            NotificationUpdate(
                priority=NotificationPriority.HIGH,
            ),
        )

    assert exc.value.status_code == 400


def test_read_status_cannot_be_set_through_update(db_session):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
    )

    with pytest.raises(HTTPException) as exc:
        NotificationService.update(
            db_session,
            notification.id,
            NotificationUpdate(
                status=NotificationStatus.READ,
            ),
        )

    assert exc.value.status_code == 400


# -------------------------------------------------------------------
# Listing and filters
# -------------------------------------------------------------------


def test_list_notifications(db_session):
    user = create_user(db_session)

    create_notification(
        db_session,
        user.id,
        event_key="list-1",
    )

    create_notification(
        db_session,
        user.id,
        event_key="list-2",
    )

    result = NotificationService.list(
        db_session,
        user_id=user.id,
    )

    assert result["total"] == 2
    assert len(result["items"]) == 2


def test_list_notifications_filter_by_type(db_session):
    user = create_user(db_session)

    create_notification(
        db_session,
        user.id,
        notification_type=NotificationType.TICKET_CREATED,
        event_key="type-1",
    )

    create_notification(
        db_session,
        user.id,
        notification_type=NotificationType.GENERAL,
        event_key="type-2",
    )

    result = NotificationService.list(
        db_session,
        user_id=user.id,
        notification_type=NotificationType.TICKET_CREATED,
    )

    assert result["total"] == 1
    assert (
        result["items"][0].notification_type
        == NotificationType.TICKET_CREATED
    )


def test_list_notifications_filter_by_priority(db_session):
    user = create_user(db_session)

    create_notification(
        db_session,
        user.id,
        priority=NotificationPriority.CRITICAL,
        event_key="priority-1",
    )

    create_notification(
        db_session,
        user.id,
        priority=NotificationPriority.LOW,
        event_key="priority-2",
    )

    result = NotificationService.list(
        db_session,
        user_id=user.id,
        priority=NotificationPriority.CRITICAL,
    )

    assert result["total"] == 1


def test_list_notifications_filter_by_channel(db_session):
    user = create_user(db_session)

    create_notification(
        db_session,
        user.id,
        channel=NotificationChannel.EMAIL,
        event_key="channel-1",
    )

    create_notification(
        db_session,
        user.id,
        channel=NotificationChannel.IN_APP,
        event_key="channel-2",
    )

    result = NotificationService.list(
        db_session,
        user_id=user.id,
        channel=NotificationChannel.EMAIL,
    )

    assert result["total"] == 1


def test_list_notifications_filter_by_read_status(db_session):
    user = create_user(db_session)

    first = create_notification(
        db_session,
        user.id,
        event_key="read-filter-1",
    )

    create_notification(
        db_session,
        user.id,
        event_key="read-filter-2",
    )

    NotificationService.mark_as_read(
        db_session,
        first.id,
    )

    unread = NotificationService.list(
        db_session,
        user_id=user.id,
        is_read=False,
    )

    read = NotificationService.list(
        db_session,
        user_id=user.id,
        is_read=True,
    )

    assert unread["total"] == 1
    assert read["total"] == 1


def test_search_notifications(db_session):
    user = create_user(db_session)

    create_notification(
        db_session,
        user.id,
        title="Network outage alert",
        message="Tower service has been interrupted.",
        event_key="search-1",
    )

    create_notification(
        db_session,
        user.id,
        title="Billing reminder",
        message="Your bill is ready.",
        event_key="search-2",
    )

    result = NotificationService.list(
        db_session,
        user_id=user.id,
        search="outage",
    )

    assert result["total"] == 1


# -------------------------------------------------------------------
# Pagination
# -------------------------------------------------------------------


def test_notification_pagination(db_session):
    user = create_user(db_session)

    for index in range(5):
        create_notification(
            db_session,
            user.id,
            event_key=f"pagination-{index}",
        )

    result = NotificationService.list(
        db_session,
        user_id=user.id,
        page=1,
        page_size=2,
    )

    assert result["total"] == 5
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert result["pages"] == 3
    assert len(result["items"]) == 2


def test_invalid_page_rejected(db_session):
    user = create_user(db_session)

    with pytest.raises(HTTPException) as exc:
        NotificationService.list(
            db_session,
            user_id=user.id,
            page=0,
        )

    assert exc.value.status_code == 400


def test_invalid_page_size_rejected(db_session):
    user = create_user(db_session)

    with pytest.raises(HTTPException) as exc:
        NotificationService.list(
            db_session,
            user_id=user.id,
            page_size=101,
        )

    assert exc.value.status_code == 400


# -------------------------------------------------------------------
# Notification event types
# -------------------------------------------------------------------


@pytest.mark.parametrize(
    "notification_type",
    [
        NotificationType.TICKET_CREATED,
        NotificationType.TICKET_ASSIGNED,
        NotificationType.TICKET_STATUS_CHANGED,
        NotificationType.SLA_RESPONSE_BREACH,
        NotificationType.SLA_RESOLUTION_BREACH,
        NotificationType.NETWORK_OUTAGE_STARTED,
        NotificationType.NETWORK_OUTAGE_RESTORED,
        NotificationType.SERVICE_REQUEST_SUBMITTED,
        NotificationType.SERVICE_REQUEST_APPROVED,
        NotificationType.SERVICE_REQUEST_REJECTED,
        NotificationType.SERVICE_REQUEST_COMPLETED,
        NotificationType.SUBSCRIPTION_ACTIVATED,
        NotificationType.SUBSCRIPTION_CANCELLED,
        NotificationType.GENERAL,
    ],
)
def test_all_notification_types_supported(
    db_session,
    notification_type,
):
    user = create_user(db_session)

    notification = create_notification(
        db_session,
        user.id,
        notification_type=notification_type,
        event_key=f"event-type-{notification_type.value}",
    )

    assert notification.notification_type == notification_type