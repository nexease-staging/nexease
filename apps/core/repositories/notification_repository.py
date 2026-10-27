from datetime import datetime

from mongoengine.errors import (
    NotUniqueError,
)

from apps.core.notification_models import (
    Notification,
)
from apps.core.notification_models import Notification


class NotificationRepository:

    @staticmethod
    def create(
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
        notification = Notification(
            organization=organization,
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            action_url=action_url,
            background_job_key=background_job_key,
            created_at=datetime.utcnow(),
        )

        try:
            notification.save()

        except NotUniqueError:
            if not background_job_key:
                raise

            existing = (
                Notification.objects(
                    organization=organization,
                    background_job_key=
                        background_job_key,
                )
                .first()
            )

            if existing is None:
                raise

            return existing

        return notification

    @staticmethod
    def get_by_id(
        *,
        organization,
        notification_id,
    ):
        return Notification.objects(
            organization=organization,
            id=notification_id,
        ).first()

    @staticmethod
    def get_by_background_job_key(
        *,
        organization,
        background_job_key,
    ):
        if not background_job_key:
            return None

        return Notification.objects(
            organization=organization,
            background_job_key=background_job_key,
        ).first()

    @staticmethod
    def list_for_recipient(
        *,
        organization,
        recipient,
        is_read=None,
        limit=50,
    ):
        queryset = Notification.objects(
            organization=organization,
            recipient=recipient,
        )

        if is_read is not None:
            queryset = queryset.filter(
                is_read=is_read,
            )

        return queryset.order_by(
            "-created_at"
        ).limit(
            limit
        )

    @staticmethod
    def mark_read(
        *,
        notification,
    ):
        if notification.is_read:
            return notification

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        notification.save()

        return notification