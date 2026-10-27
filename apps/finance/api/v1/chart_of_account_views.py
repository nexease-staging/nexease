import json

from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)
from apps.core.services.api_query_pipeline_service import (
    APIQueryPipelineError,
    APIQueryPipelineService,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.finance.api.v1.serializers import (
    ChartOfAccountAPISerializer,
)
from apps.finance.repositories.chart_of_account_repository import (
    ChartOfAccountRepository,
)
from apps.finance.services.chart_of_account_api_service import (
    ChartOfAccountAPIService,
    ChartOfAccountAPIStateError,
    ChartOfAccountAPIValidationError,
)


def _json_body(
    request,
):
    content_type = (
        request.content_type
        or
        ""
    ).lower()

    if (
        "application/json"
        not in content_type
    ):
        return (
            None,
            APIResponseService
            .validation_error(
                message=(
                    "Content-Type must be "
                    "application/json."
                ),
                details={
                    "content_type": [
                        (
                            "Send the request body "
                            "as JSON."
                        ),
                    ],
                },
                request=request,
            ),
        )

    try:
        return (
            json.loads(
                request.body
                or
                b"{}"
            ),
            None,
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return (
            None,
            APIResponseService
            .validation_error(
                message="Malformed JSON body.",
                details={
                    "body": [
                        (
                            "Request body must "
                            "contain valid JSON."
                        ),
                    ],
                },
                request=request,
            ),
        )


@api_login_required
@api_rate_limit(
    scope="chart_of_accounts.collection",
    limit=120,
    window_seconds=60,
)
def chart_of_account_collection_api(
    request,
):
    if request.method == "GET":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "chart_of_accounts.read",
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        queryset = (
            ChartOfAccountRepository
            .queryset_for_organization(
                organization=(
                    request.api_organization
                ),
            )
        )

        try:
            pipeline_result = (
                APIQueryPipelineService
                .execute(
                    queryset,
                    request,
                    allowed_filters={
                        "account_type": {
                            "field":
                                "account_type",
                            "parser":
                                "string",
                        },
                        "account_subtype": {
                            "field":
                                "account_subtype",
                            "parser":
                                "string",
                        },
                        "normal_balance": {
                            "field":
                                "normal_balance",
                            "parser":
                                "string",
                        },
                        "is_system_account": {
                            "field":
                                "is_system_account",
                            "parser":
                                "boolean",
                        },
                        "is_active": {
                            "field":
                                "is_active",
                            "parser":
                                "boolean",
                        },
                        "allow_manual_posting": {
                            "field": (
                                "allow_manual_posting"
                            ),
                            "parser":
                                "boolean",
                        },
                    },
                    search_fields=[
                        "account_code",
                        "account_name",
                        "account_subtype",
                        "system_key",
                        "description",
                    ],
                    allowed_sort_fields={
                        "account_code":
                            "account_code",
                        "account_name":
                            "account_name",
                        "account_type":
                            "account_type",
                        "account_subtype":
                            "account_subtype",
                        "normal_balance":
                            "normal_balance",
                        "is_active":
                            "is_active",
                        "created_at":
                            "created_at",
                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "account_code",
                    ],
                    stable_sort_field="id",
                    default_page_size=25,
                    maximum_page_size=100,
                )
            )

        except APIQueryPipelineError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details={
                        "component":
                            exc.component,
                        "fields":
                            exc.details,
                    },
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "accounts": (
                        ChartOfAccountAPISerializer
                        .serialize_many(
                            pipeline_result[
                                "items"
                            ]
                        )
                    ),
                    "pagination":
                        pipeline_result[
                            "pagination"
                        ],
                    "query":
                        pipeline_result[
                            "query"
                        ],
                },
                request=request,
            )
        )

    if request.method == "POST":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "chart_of_accounts.create",
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        payload, error_response = (
            _json_body(
                request
            )
        )

        if error_response:
            return error_response

        try:
            account = (
                ChartOfAccountAPIService
                .create_account(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except (
            ChartOfAccountAPIValidationError
        ) as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except (
            ChartOfAccountAPIStateError
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

        return (
            APIResponseService
            .success(
                data={
                    "account": (
                        ChartOfAccountAPISerializer
                        .serialize_detail(
                            account
                        )
                    ),
                },
                message=(
                    "Chart of account created "
                    "successfully."
                ),
                status=201,
                request=request,
            )
        )

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET to list accounts or "
                "POST to create an account."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="chart_of_accounts.detail",
    limit=120,
    window_seconds=60,
)
def chart_of_account_detail_api(
    request,
    account_id,
):
    if request.method == "GET":
        permission_code = (
            "chart_of_accounts.read"
        )

    elif request.method == "PATCH":
        permission_code = (
            "chart_of_accounts.update"
        )

    else:
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve an "
                    "account or PATCH to update it."
                ),
                request=request,
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

    if request.method == "GET":
        try:
            account = (
                ChartOfAccountAPIService
                .get_account(
                    organization=(
                        request.api_organization
                    ),
                    account_id=account_id,
                )
            )

        except (
            ChartOfAccountAPIValidationError
        ) as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except LookupError:
            return (
                APIResponseService
                .not_found(
                    message=(
                        "Chart of account "
                        "not found."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "account": (
                        ChartOfAccountAPISerializer
                        .serialize_detail(
                            account
                        )
                    ),
                },
                request=request,
            )
        )

    payload, error_response = (
        _json_body(
            request
        )
    )

    if error_response:
        return error_response

    try:
        account = (
            ChartOfAccountAPIService
            .update_account(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                account_id=account_id,
                payload=payload,
            )
        )

    except (
        ChartOfAccountAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message=(
                    "Chart of account not found."
                ),
                request=request,
            )
        )

    except (
        ChartOfAccountAPIStateError
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

    return (
        APIResponseService
        .success(
            data={
                "account": (
                    ChartOfAccountAPISerializer
                    .serialize_detail(
                        account
                    )
                ),
            },
            message=(
                "Chart of account updated "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="chart_of_accounts.deactivate",
    limit=60,
    window_seconds=60,
)
def chart_of_account_deactivate_api(
    request,
    account_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to deactivate "
                    "an account."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "chart_of_accounts.deactivate",
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
        account = (
            ChartOfAccountAPIService
            .deactivate_account(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                account_id=account_id,
            )
        )

    except (
        ChartOfAccountAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message=(
                    "Chart of account not found."
                ),
                request=request,
            )
        )

    except (
        ChartOfAccountAPIStateError
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

    return (
        APIResponseService
        .success(
            data={
                "account": (
                    ChartOfAccountAPISerializer
                    .serialize_detail(
                        account
                    )
                ),
            },
            message=(
                "Chart of account deactivated "
                "successfully."
            ),
            request=request,
        )
    )