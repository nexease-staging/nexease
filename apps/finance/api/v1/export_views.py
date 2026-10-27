from django.http import HttpResponse

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
from apps.finance.services.accounting_report_api_service import (
    AccountingReportAPIStateError,
    AccountingReportAPIValidationError,
)
from apps.finance.services.export_api_service import (
    ExportAPIService,
    ExportAPIValidationError,
)
from apps.finance.services.financial_report_api_service import (
    FinancialReportAPIStateError,
    FinancialReportAPIValidationError,
)


@api_login_required
@api_rate_limit(
    scope="exports.read",
    limit=60,
    window_seconds=60,
)
def export_api(
    request,
    resource_type,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to export data."
                ),
                request=request,
            )
        )

    try:
        normalized_resource = (
            ExportAPIService
            .normalize_resource_type(
                resource_type
            )
        )

        permission_code = (
            ExportAPIService
            .get_permission(
                normalized_resource
            )
        )

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                permission_code,
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        parameters = {
            key: value
            for key, value
            in request.GET.items()
            if key != "format"
        }

        result = (
            ExportAPIService
            .export(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                resource_type=(
                    normalized_resource
                ),
                export_format=(
                    request.GET.get(
                        "format",
                        "csv",
                    )
                ),
                parameters=parameters,
            )
        )

    except ExportAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except (
        AccountingReportAPIValidationError,
        FinancialReportAPIValidationError,
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError as exc:
        return (
            APIResponseService
            .not_found(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except (
        AccountingReportAPIStateError,
        FinancialReportAPIStateError,
    ) as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
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
                    "Export generation failed."
                ),
                request=request,
            )
        )

    response = HttpResponse(
        result[
            "content"
        ],
        content_type=result[
            "content_type"
        ],
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; filename="'
        f'{result["filename"]}'
        '"'
    )

    response[
        "Content-Length"
    ] = str(
        result[
            "size"
        ]
    )

    return response