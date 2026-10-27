from apps.core.notification_models import Notification
from apps.core.repositories.notification_repository import (
    NotificationRepository,
)


class NotificationService:

    @staticmethod
    def create_notification(
        *,
        organization,
        recipient,
        notification_type,
        title,
        message,
        severity="INFO",
        resource_type=None,
        resource_id=None,
        action_url=None,
        background_job_key=None,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not recipient:
            raise ValueError(
                "Recipient is required."
            )

        if not recipient.is_active:
            raise ValueError(
                "Recipient is inactive."
            )

        if (
            str(recipient.organization.id)
            !=
            str(organization.id)
        ):
            raise PermissionError(
                "Recipient does not belong "
                "to this organization."
            )

        normalized_type = str(
            notification_type or ""
        ).strip().upper()

        if (
            normalized_type
            not in Notification.NOTIFICATION_TYPES
        ):
            raise ValueError(
                "Invalid notification type."
            )

        normalized_severity = str(
            severity or "INFO"
        ).strip().upper()

        if (
            normalized_severity
            not in Notification.SEVERITIES
        ):
            raise ValueError(
                "Invalid notification severity."
            )

        normalized_title = str(
            title or ""
        ).strip()

        if not normalized_title:
            raise ValueError(
                "Notification title is required."
            )

        if len(normalized_title) > 200:
            raise ValueError(
                "Notification title is too long."
            )

        normalized_message = str(
            message or ""
        ).strip()

        if not normalized_message:
            raise ValueError(
                "Notification message is required."
            )

        if len(normalized_message) > 1000:
            raise ValueError(
                "Notification message is too long."
            )

        normalized_job_key = (
            str(background_job_key).strip()
            if background_job_key
            else None
        )

        if normalized_job_key:

            existing = (
                NotificationRepository
                .get_by_background_job_key(
                    organization=organization,
                    background_job_key=
                        normalized_job_key,
                )
            )

            if existing:
                return existing

        return (
            NotificationRepository
            .create(
                organization=organization,
                recipient=recipient,
                notification_type=
                    normalized_type,
                title=normalized_title,
                message=normalized_message,
                severity=normalized_severity,
                resource_type=(
                    str(resource_type).strip()
                    if resource_type
                    else None
                ),
                resource_id=(
                    str(resource_id).strip()
                    if resource_id
                    else None
                ),
                action_url=(
                    str(action_url).strip()
                    if action_url
                    else None
                ),
                background_job_key=
                    normalized_job_key,
            )
        )

    @staticmethod
    def list_for_user(
        *,
        user,
        is_read=None,
        limit=50,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        return (
            NotificationRepository
            .list_for_recipient(
                organization=
                    user.organization,
                recipient=user,
                is_read=is_read,
                limit=limit,
            )
        )

    @staticmethod
    def mark_read(
        *,
        user,
        notification_id,
    ):
        notification = (
            NotificationRepository
            .get_by_id(
                organization=
                    user.organization,
                notification_id=
                    notification_id,
            )
        )

        if notification is None:
            raise LookupError(
                "Notification not found."
            )

        if (
            str(notification.recipient.id)
            !=
            str(user.id)
        ):
            raise PermissionError(
                "Notification does not belong "
                "to this user."
            )

        return (
            NotificationRepository
            .mark_read(
                notification=notification,
            )
        )