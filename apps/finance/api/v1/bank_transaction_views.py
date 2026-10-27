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
    BankTransactionAPISerializer,
)
from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)
from apps.finance.services.bank_transaction_api_service import (
    BankTransactionAPIService,
    BankTransactionAPIStateError,
    BankTransactionAPIValidationError,
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
    scope="bank_transactions.collection",
    limit=120,
    window_seconds=60,
)
def bank_transaction_collection_api(
    request,
):
    if request.method == "GET":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "bank_transactions.read",
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
            BankTransactionRepository
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
                        "bank_account_id": {
                            "field":
                                "bank_account",
                            "parser":
                                "object_id",
                        },
                        "transaction_type": {
                            "field":
                                "transaction_type",
                            "parser":
                                "string",
                        },
                        "reconciliation_status": {
                            "field": (
                                "reconciliation_status"
                            ),
                            "parser":
                                "string",
                        },
                    },
                    search_fields=[
                        "transaction_number",
                        "external_reference",
                        "reference_type",
                        "reference_id",
                        "description",
                    ],
                    allowed_sort_fields={
                        "transaction_number":
                            "transaction_number",
                        "transaction_type":
                            "transaction_type",
                        "transaction_date":
                            "transaction_date",
                        "amount":
                            "amount",
                        "balance_before":
                            "balance_before",
                        "balance_after":
                            "balance_after",
                        "reconciliation_status": (
                            "reconciliation_status"
                        ),
                        "created_at":
                            "created_at",
                    },
                    default_sort=[
                        "-transaction_date",
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
                    "bank_transactions": (
                        BankTransactionAPISerializer
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
                "bank_transactions.create",
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
            transaction = (
                BankTransactionAPIService
                .create_transaction(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except (
            BankTransactionAPIValidationError
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
            BankTransactionAPIStateError
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
                    "bank_transaction": (
                        BankTransactionAPISerializer
                        .serialize_detail(
                            transaction
                        )
                    ),
                },
                message=(
                    "Bank transaction created "
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
                "Use GET to list bank "
                "transactions or POST to "
                "create one."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="bank_transactions.detail",
    limit=120,
    window_seconds=60,
)
def bank_transaction_detail_api(
    request,
    transaction_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve a "
                    "bank transaction."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "bank_transactions.read",
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
        transaction = (
            BankTransactionAPIService
            .get_transaction(
                organization=(
                    request.api_organization
                ),
                transaction_id=(
                    transaction_id
                ),
            )
        )

    except (
        BankTransactionAPIValidationError
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
                    "Bank transaction not found."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "bank_transaction": (
                    BankTransactionAPISerializer
                    .serialize_detail(
                        transaction
                    )
                ),
            },
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="bank_transactions.reconcile",
    limit=60,
    window_seconds=60,
)
def bank_transaction_reconcile_api(
    request,
    transaction_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to reconcile a "
                    "bank transaction."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "bank_transactions.reconcile",
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
        transaction = (
            BankTransactionAPIService
            .reconcile_transaction(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                transaction_id=(
                    transaction_id
                ),
            )
        )

    except (
        BankTransactionAPIValidationError
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
                    "Bank transaction not found."
                ),
                request=request,
            )
        )

    except (
        BankTransactionAPIStateError
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
                "bank_transaction": (
                    BankTransactionAPISerializer
                    .serialize_detail(
                        transaction
                    )
                ),
            },
            message=(
                "Bank transaction reconciled "
                "successfully."
            ),
            request=request,
        )
    )