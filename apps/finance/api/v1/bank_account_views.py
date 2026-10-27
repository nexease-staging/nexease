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
    BankAccountAPISerializer,
)
from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.finance.services.bank_account_api_service import (
    BankAccountAPIService,
    BankAccountAPIStateError,
    BankAccountAPIValidationError,
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
    scope="bank_accounts.collection",
    limit=120,
    window_seconds=60,
)
def bank_account_collection_api(
    request,
):
    if request.method == "GET":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "bank_accounts.read",
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
            BankAccountRepository
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
                        "currency": {
                            "field":
                                "currency",
                            "parser":
                                "string",
                        },
                        "is_active": {
                            "field":
                                "is_active",
                            "parser":
                                "boolean",
                        },
                    },
                    search_fields=[
                        "account_name",
                        "bank_name",
                        "account_number",
                        "ifsc_code",
                        "currency",
                    ],
                    allowed_sort_fields={
                        "account_name":
                            "account_name",
                        "account_type":
                            "account_type",
                        "bank_name":
                            "bank_name",
                        "currency":
                            "currency",
                        "opening_balance":
                            "opening_balance",
                        "current_balance":
                            "current_balance",
                        "is_active":
                            "is_active",
                        "created_at":
                            "created_at",
                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "account_name",
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
                    "bank_accounts": (
                        BankAccountAPISerializer
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
                "bank_accounts.create",
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
            bank_account = (
                BankAccountAPIService
                .create_bank_account(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except (
            BankAccountAPIValidationError
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
            BankAccountAPIStateError
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
                    "bank_account": (
                        BankAccountAPISerializer
                        .serialize_detail(
                            bank_account
                        )
                    ),
                },
                message=(
                    "Bank account created "
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
                "Use GET to list bank accounts "
                "or POST to create one."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="bank_accounts.detail",
    limit=120,
    window_seconds=60,
)
def bank_account_detail_api(
    request,
    bank_account_id,
):
    if request.method == "GET":
        permission_code = (
            "bank_accounts.read"
        )

    elif request.method == "PATCH":
        permission_code = (
            "bank_accounts.update"
        )

    else:
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve a bank "
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
            bank_account = (
                BankAccountAPIService
                .get_bank_account(
                    organization=(
                        request.api_organization
                    ),
                    bank_account_id=(
                        bank_account_id
                    ),
                )
            )

        except (
            BankAccountAPIValidationError
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
                        "Bank account not found."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "bank_account": (
                        BankAccountAPISerializer
                        .serialize_detail(
                            bank_account
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
        bank_account = (
            BankAccountAPIService
            .update_bank_account(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                bank_account_id=(
                    bank_account_id
                ),
                payload=payload,
            )
        )

    except (
        BankAccountAPIValidationError
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
                message="Bank account not found.",
                request=request,
            )
        )

    except (
        BankAccountAPIStateError
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
                "bank_account": (
                    BankAccountAPISerializer
                    .serialize_detail(
                        bank_account
                    )
                ),
            },
            message=(
                "Bank account updated "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="bank_accounts.deactivate",
    limit=60,
    window_seconds=60,
)
def bank_account_deactivate_api(
    request,
    bank_account_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to deactivate "
                    "a bank account."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "bank_accounts.deactivate",
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
        bank_account = (
            BankAccountAPIService
            .deactivate_bank_account(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

    except (
        BankAccountAPIValidationError
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
                message="Bank account not found.",
                request=request,
            )
        )

    except (
        BankAccountAPIStateError
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
                "bank_account": (
                    BankAccountAPISerializer
                    .serialize_detail(
                        bank_account
                    )
                ),
            },
            message=(
                "Bank account deactivated "
                "successfully."
            ),
            request=request,
        )
    )