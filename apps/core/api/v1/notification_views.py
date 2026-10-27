from apps.core.api.decorators import (
    api_login_required,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.core.services.notification_service import (
    NotificationService,
)


def _iso(value):
    if value is None:
        return None

    return value.isoformat()


def _serialize_notification(
    notification,
):
    return {
        "id": str(notification.id),
        "notification_type":
            notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "severity": notification.severity,
        "resource_type":
            notification.resource_type,
        "resource_id":
            notification.resource_id,
        "action_url":
            notification.action_url,
        "is_read": notification.is_read,
        "read_at": _iso(
            notification.read_at
        ),
        "created_at": _iso(
            notification.created_at
        ),
    }


def _parse_is_read(
    value,
):
    if value is None or value == "":
        return None

    normalized = (
        str(value)
        .strip()
        .lower()
    )

    if normalized in {
        "true",
        "1",
        "yes",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
    }:
        return False

    raise ValueError(
        "is_read must be true or false."
    )


@api_login_required
def notification_list_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "notifications."
                ),
                request=request,
            )
        )

    try:
        is_read = _parse_is_read(
            request.GET.get(
                "is_read"
            )
        )

        limit = request.GET.get(
            "limit",
            50,
        )

        try:
            limit = int(limit)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "Limit must be an integer."
            ) from exc

        if limit < 1 or limit > 100:
            raise ValueError(
                "Limit must be between "
                "1 and 100."
            )

        notifications = (
            NotificationService
            .list_for_user(
                user=request.api_user,
                is_read=is_read,
                limit=limit,
            )
        )

        results = [
            _serialize_notification(
                notification
            )
            for notification
            in notifications
        ]

        unread_count = sum(
            1
            for notification
            in results
            if not notification["is_read"]
        )

        return (
            APIResponseService
            .success(
                data={
                    "results": results,
                    "count": len(results),
                    "unread_count":
                        unread_count,
                },
                message=(
                    "Notifications retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    except ValueError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(exc),
                request=request,
            )
        )


@api_login_required
def notification_read_api(
    request,
    notification_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to mark "
                    "a notification as read."
                ),
                request=request,
            )
        )

    try:
        notification = (
            NotificationService
            .mark_read(
                user=request.api_user,
                notification_id=
                    notification_id,
            )
        )

        return (
            APIResponseService
            .success(
                data=(
                    _serialize_notification(
                        notification
                    )
                ),
                message=(
                    "Notification marked "
                    "as read."
                ),
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message=(
                    "Notification not found."
                ),
                request=request,
            )
        )

    except PermissionError as exc:
        return (
            APIResponseService
            .forbidden(
                message=str(exc),
                request=request,
            )
        )

    except ValueError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(exc),
                request=request,
            )
        )
