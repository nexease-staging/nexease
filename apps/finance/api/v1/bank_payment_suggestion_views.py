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
    BankPaymentSuggestionAPISerializer,
)
from apps.finance.repositories.bank_payment_suggestion_repository import (
    BankPaymentSuggestionRepository,
)
from apps.finance.services.bank_payment_suggestion_api_service import (
    BankPaymentSuggestionAPIService,
    BankPaymentSuggestionAPIStateError,
    BankPaymentSuggestionAPIValidationError,
)


def _error_response(
    request,
    exc,
):
    if isinstance(
        exc,
        BankPaymentSuggestionAPIValidationError,
    ):
        return APIResponseService.validation_error(
            message=exc.message,
            details=exc.details,
            request=request,
        )

    if isinstance(
        exc,
        LookupError,
    ):
        return APIResponseService.not_found(
            message=(
                str(exc)
                or
                "Payment suggestion not found."
            ),
            request=request,
        )

    if isinstance(
        exc,
        BankPaymentSuggestionAPIStateError,
    ):
        return APIResponseService.unprocessable_entity(
            message=exc.message,
            details=exc.details,
            request=request,
        )

    return APIResponseService.forbidden(
        message="Permission denied.",
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_payment_suggestions.collection",
    limit=120,
    window_seconds=60,
)
def bank_payment_suggestion_collection_api(
    request,
):
    if request.method != "GET":
        return APIResponseService.method_not_allowed(
            message=(
                "Use GET to list bank payment "
                "suggestions."
            ),
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "bank_statements.read",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    queryset = (
        BankPaymentSuggestionRepository
        .queryset_for_organization(
            organization=request.api_organization,
        )
    )

    try:
        pipeline_result = (
            APIQueryPipelineService
            .execute(
                queryset,
                request,
                allowed_filters={
                    "statement_id": {
                        "field": "statement",
                        "parser": "object_id",
                    },
                    "invoice_id": {
                        "field": "invoice",
                        "parser": "object_id",
                    },
                    "vendor_bill_id": {
                        "field": "vendor_bill",
                        "parser": "object_id",
                    },
                    "suggestion_type": {
                        "field": "suggestion_type",
                        "parser": "string",
                    },
                    "status": {
                        "field": "status",
                        "parser": "string",
                    },
                },
                search_fields=[
                    "line_number",
                    "match_reason",
                    "payment_reference",
                ],
                allowed_sort_fields={
                    "line_number": "line_number",
                    "suggestion_type": "suggestion_type",
                    "amount": "amount",
                    "confidence": "confidence",
                    "status": "status",
                    "created_at": "created_at",
                    "updated_at": "updated_at",
                },
                default_sort=[
                    "-created_at",
                ],
                stable_sort_field="id",
                default_page_size=25,
                maximum_page_size=100,
            )
        )

    except APIQueryPipelineError as exc:
        return APIResponseService.validation_error(
            message=exc.message,
            details={
                "component": exc.component,
                "fields": exc.details,
            },
            request=request,
        )

    return APIResponseService.success(
        data={
            "bank_payment_suggestions": (
                BankPaymentSuggestionAPISerializer
                .serialize_many(
                    pipeline_result["items"]
                )
            ),
            "pagination": (
                pipeline_result["pagination"]
            ),
            "query": pipeline_result["query"],
        },
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_payment_suggestions.detail",
    limit=120,
    window_seconds=60,
)
def bank_payment_suggestion_detail_api(
    request,
    suggestion_id,
):
    if request.method != "GET":
        return APIResponseService.method_not_allowed(
            message=(
                "Use GET to retrieve a bank "
                "payment suggestion."
            ),
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "bank_statements.read",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        suggestion = (
            BankPaymentSuggestionAPIService
            .get_suggestion(
                organization=request.api_organization,
                suggestion_id=suggestion_id,
            )
        )

    except (
        BankPaymentSuggestionAPIValidationError,
        LookupError,
    ) as exc:
        return _error_response(
            request,
            exc,
        )

    return APIResponseService.success(
        data={
            "bank_payment_suggestion": (
                BankPaymentSuggestionAPISerializer
                .serialize_detail(
                    suggestion
                )
            ),
        },
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_payment_suggestions.generate",
    limit=120,
    window_seconds=60,
)
def bank_payment_suggestion_generate_api(
    request,
    statement_id,
    line_number,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message=(
                "Use POST to generate a payment "
                "suggestion."
            ),
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "bank_statements.reconcile",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        suggestion = (
            BankPaymentSuggestionAPIService
            .generate_suggestion(
                user=request.api_user,
                organization=request.api_organization,
                statement_id=statement_id,
                line_number=line_number,
            )
        )

    except (
        BankPaymentSuggestionAPIValidationError,
        BankPaymentSuggestionAPIStateError,
        LookupError,
        PermissionError,
    ) as exc:
        return _error_response(
            request,
            exc,
        )

    return APIResponseService.success(
        data={
            "bank_payment_suggestion": (
                BankPaymentSuggestionAPISerializer
                .serialize_detail(
                    suggestion
                )
            ),
        },
        message=(
            "Bank payment suggestion generated "
            "successfully."
        ),
        status=201,
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_payment_suggestions.confirm",
    limit=120,
    window_seconds=60,
)
def bank_payment_suggestion_confirm_api(
    request,
    suggestion_id,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message=(
                "Use POST to confirm a bank "
                "payment suggestion."
            ),
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "bank_statements.reconcile",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        suggestion = (
            BankPaymentSuggestionAPIService
            .confirm_suggestion(
                user=request.api_user,
                organization=request.api_organization,
                suggestion_id=suggestion_id,
            )
        )

    except (
        BankPaymentSuggestionAPIValidationError,
        BankPaymentSuggestionAPIStateError,
        LookupError,
        PermissionError,
    ) as exc:
        return _error_response(
            request,
            exc,
        )

    return APIResponseService.success(
        data={
            "bank_payment_suggestion": (
                BankPaymentSuggestionAPISerializer
                .serialize_detail(
                    suggestion
                )
            ),
        },
        message=(
            "Bank payment suggestion confirmed "
            "successfully."
        ),
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_payment_suggestions.reject",
    limit=120,
    window_seconds=60,
)
def bank_payment_suggestion_reject_api(
    request,
    suggestion_id,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message=(
                "Use POST to reject a bank "
                "payment suggestion."
            ),
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "bank_statements.reconcile",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        suggestion = (
            BankPaymentSuggestionAPIService
            .reject_suggestion(
                user=request.api_user,
                organization=request.api_organization,
                suggestion_id=suggestion_id,
            )
        )

    except (
        BankPaymentSuggestionAPIValidationError,
        BankPaymentSuggestionAPIStateError,
        LookupError,
        PermissionError,
    ) as exc:
        return _error_response(
            request,
            exc,
        )

    return APIResponseService.success(
        data={
            "bank_payment_suggestion": (
                BankPaymentSuggestionAPISerializer
                .serialize_detail(
                    suggestion
                )
            ),
        },
        message=(
            "Bank payment suggestion rejected "
            "successfully."
        ),
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_payment_suggestions.execute",
    limit=60,
    window_seconds=60,
)
def bank_payment_suggestion_execute_api(
    request,
    suggestion_id,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message=(
                "Use POST to execute a bank "
                "payment suggestion."
            ),
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "bank_statements.reconcile",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        result = (
            BankPaymentSuggestionAPIService
            .execute_suggestion(
                user=request.api_user,
                organization=request.api_organization,
                suggestion_id=suggestion_id,
            )
        )

    except (
        BankPaymentSuggestionAPIValidationError,
        BankPaymentSuggestionAPIStateError,
        LookupError,
        PermissionError,
    ) as exc:
        return _error_response(
            request,
            exc,
        )

    return APIResponseService.success(
        data={
            "execution": (
                BankPaymentSuggestionAPISerializer
                .serialize_execution(
                    result
                )
            ),
        },
        message=(
            "Bank payment suggestion executed "
            "successfully."
        ),
        request=request,
    )
