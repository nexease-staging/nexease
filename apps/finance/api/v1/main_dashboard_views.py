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
    MainDashboardAPISerializer,
)

from apps.finance.services.main_dashboard_api_service import (
    MainDashboardAPIService,
    MainDashboardAPIValidationError,
)


@api_login_required
@api_rate_limit(
    scope="accounting_reports.read",
    limit=120,
    window_seconds=60,
)
def main_dashboard_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve the "
                    "main dashboard."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "accounting_reports.read",
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
        result = (
            MainDashboardAPIService
            .get_dashboard(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                start_date=(
                    request.GET.get(
                        "start_date"
                    )
                ),
                end_date=(
                    request.GET.get(
                        "end_date"
                    )
                ),
            )
        )

    except (
        MainDashboardAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
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

    return (
        APIResponseService
        .success(
            data={
                "dashboard": (
                    MainDashboardAPISerializer
                    .serialize(
                        result
                    )
                ),
            },
            request=request,
        )
    )