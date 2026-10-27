from apps.accounts.models import User

from apps.core.services.background_job_executor import (
    BackgroundJobExecutor,
)
from apps.core.services.notification_service import (
    NotificationService,
)


def execute_notification(
    *,
    job,
):
    payload = job.payload or {}

    recipient_id = payload.get(
        "recipient_id"
    )

    if not recipient_id:
        raise ValueError(
            "Notification recipient_id "
            "is required."
        )

    recipient = User.objects(
        id=recipient_id,
        organization=job.organization,
    ).first()

    if recipient is None:
        raise LookupError(
            "Notification recipient "
            "was not found."
        )

    notification = (
        NotificationService
        .create_notification(
            organization=
                job.organization,
            recipient=recipient,
            notification_type=
                payload.get(
                    "notification_type"
                ),
            title=
                payload.get(
                    "title"
                ),
            message=
                payload.get(
                    "message"
                ),
            severity=
                payload.get(
                    "severity",
                    "INFO",
                ),
            resource_type=
                payload.get(
                    "resource_type"
                ),
            resource_id=
                payload.get(
                    "resource_id"
                ),
            action_url=
                payload.get(
                    "action_url"
                ),
            background_job_key=
                job.idempotency_key,
        )
    )

    return {
        "notification_id":
            str(
                notification.id
            ),
        "recipient_id":
            str(
                notification.recipient.id
            ),
        "notification_type":
            notification.notification_type,
        "severity":
            notification.severity,
        "is_read":
            notification.is_read,
    }


def register_core_background_jobs():
    registered = (
        BackgroundJobExecutor
        .registered_job_types()
    )

    if (
        "NOTIFICATION"
        not in registered
    ):
        (
            BackgroundJobExecutor
            .register(
                "NOTIFICATION",
                execute_notification,
            )
        )