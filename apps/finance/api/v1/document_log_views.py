from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.finance.api.v1.serializers import (
    DocumentAccessLogAPISerializer,
    DocumentDeliveryLogAPISerializer,
)
from apps.finance.services.document_access_log_service import (
    DocumentAccessLogService,
)
from apps.finance.services.document_delivery_log_service import (
    DocumentDeliveryLogService,
)


AUDIT_PERMISSION = "accounting_audit.read"


# ============================================================
# DOCUMENT ACCESS LOGS
# ============================================================


@api_login_required
@api_rate_limit(
    scope="document_access_logs.read",
    limit=120,
    window_seconds=60,
)
def document_access_logs_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to view "
                    "document access logs."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            AUDIT_PERMISSION,
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        logs = (
            DocumentAccessLogService
            .list_logs(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                document_type=(
                    request.GET.get(
                        "document_type"
                    )
                ),
                action=(
                    request.GET.get(
                        "action"
                    )
                ),
                document_number=(
                    request.GET.get(
                        "document_number"
                    )
                ),
                user_id=(
                    request.GET.get(
                        "user_id"
                    )
                ),
                limit=(
                    request.GET.get(
                        "limit",
                        100,
                    )
                ),
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

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    except Exception:
        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to load "
                    "document access logs."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "logs": (
                    DocumentAccessLogAPISerializer
                    .serialize_many(
                        logs
                    )
                ),
            },
            message=(
                "Document access logs "
                "retrieved."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="document_access_logs.summary",
    limit=120,
    window_seconds=60,
)
def document_access_log_summary_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to view "
                    "document access summary."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            AUDIT_PERMISSION,
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        summary = (
            DocumentAccessLogService
            .get_summary(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
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

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    except Exception:
        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to load "
                    "document access summary."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "summary": summary,
            },
            message=(
                "Document access summary "
                "retrieved."
            ),
            request=request,
        )
    )


# ============================================================
# DOCUMENT DELIVERY LOGS
# ============================================================


@api_login_required
@api_rate_limit(
    scope="document_delivery_logs.read",
    limit=120,
    window_seconds=60,
)
def document_delivery_logs_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to view "
                    "document delivery logs."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            AUDIT_PERMISSION,
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        logs = (
            DocumentDeliveryLogService
            .list_logs(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                document_type=(
                    request.GET.get(
                        "document_type"
                    )
                ),
                channel=(
                    request.GET.get(
                        "channel"
                    )
                ),
                status=(
                    request.GET.get(
                        "status"
                    )
                ),
                recipient=(
                    request.GET.get(
                        "recipient"
                    )
                ),
                document_number=(
                    request.GET.get(
                        "document_number"
                    )
                ),
                subject=(
                    request.GET.get(
                        "subject"
                    )
                ),
                recipient_overridden=(
                    request.GET.get(
                        "recipient_overridden"
                    )
                ),
                custom_subject=(
                    request.GET.get(
                        "custom_subject"
                    )
                ),
                custom_message=(
                    request.GET.get(
                        "custom_message"
                    )
                ),
                limit=(
                    request.GET.get(
                        "limit",
                        100,
                    )
                ),
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

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    except Exception:
        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to load "
                    "document delivery logs."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "logs": (
                    DocumentDeliveryLogAPISerializer
                    .serialize_many(
                        logs
                    )
                ),
            },
            message=(
                "Document delivery logs "
                "retrieved."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="document_delivery_logs.summary",
    limit=120,
    window_seconds=60,
)
def document_delivery_log_summary_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to view "
                    "document delivery summary."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            AUDIT_PERMISSION,
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        summary = (
            DocumentDeliveryLogService
            .get_summary(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
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

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    except Exception:
        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to load "
                    "document delivery summary."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "summary": summary,
            },
            message=(
                "Document delivery summary "
                "retrieved."
            ),
            request=request,
        )
    )