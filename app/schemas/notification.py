from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.notification import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


class NotificationCreate(BaseModel):
    user_id: int
    notification_type: NotificationType
    channel: NotificationChannel = NotificationChannel.IN_APP
    priority: NotificationPriority = NotificationPriority.MEDIUM

    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)

    reference_type: str | None = Field(
        default=None,
        max_length=50,
    )

    reference_id: int | None = None

    event_key: str | None = Field(
        default=None,
        max_length=150,
    )

    expires_at: datetime | None = None

    @field_validator("title", "message")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty")

        return value


class NotificationUpdate(BaseModel):
    priority: NotificationPriority | None = None
    status: NotificationStatus | None = None
    expires_at: datetime | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

    notification_type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    status: NotificationStatus

    title: str
    message: str

    reference_type: str | None
    reference_id: int | None
    event_key: str | None

    is_read: bool

    sent_at: datetime | None
    read_at: datetime | None
    expires_at: datetime | None

    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class NotificationReadResponse(BaseModel):
    id: int
    is_read: bool
    read_at: datetime | None