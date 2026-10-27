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
    BankStatementAPISerializer,
    BankTransactionAPISerializer,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.core.services.background_upload_service import (
    BackgroundUploadService,
)
from apps.finance.repositories.bank_statement_repository import (
    BankStatementRepository,
)
from apps.finance.services.bank_statement_api_service import (
    BankStatementAPIService,
    BankStatementAPIStateError,
    BankStatementAPIValidationError,
)




def _json_body(
    request,
):
    content_type = (
        request.content_type
        or
        ""
    ).lower()

    if "application/json" not in content_type:
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
                        "Send the request body as JSON.",
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
                        "Request body must contain valid JSON.",
                    ],
                },
                request=request,
            ),
        )


@api_login_required
@api_rate_limit(
    scope="bank_statements.collection",
    limit=60,
    window_seconds=60,
)
def bank_statement_collection_api(
    request,
):
    if request.method == "GET":
        if not AuthorizationService.has_permission(
            request.api_user,
            "bank_statements.read",
        ):
            return APIResponseService.forbidden(
                message="Permission denied.",
                request=request,
            )

        queryset = (
            BankStatementRepository
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
                        "bank_account_id": {
                            "field": "bank_account",
                            "parser": "object_id",
                        },
                        "status": {
                            "field": "status",
                            "parser": "string",
                        },
                        "source_type": {
                            "field": "source_type",
                            "parser": "string",
                        },
                    },
                    search_fields=[
                        "statement_number",
                        "source_filename",
                    ],
                    allowed_sort_fields={
                        "statement_number": "statement_number",
                        "statement_start_date": "statement_start_date",
                        "statement_end_date": "statement_end_date",
                        "opening_balance": "opening_balance",
                        "closing_balance": "closing_balance",
                        "status": "status",
                        "source_type": "source_type",
                        "created_at": "created_at",
                        "updated_at": "updated_at",
                    },
                    default_sort=[
                        "-statement_start_date",
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
                "bank_statements": (
                    BankStatementAPISerializer
                    .serialize_many(
                        pipeline_result["items"]
                    )
                ),
                "pagination": pipeline_result["pagination"],
                "query": pipeline_result["query"],
            },
            request=request,
        )

    if request.method == "POST":
        if not AuthorizationService.has_permission(
            request.api_user,
            "bank_statements.create",
        ):
            return APIResponseService.forbidden(
                message="Permission denied.",
                request=request,
            )

        uploaded_file = request.FILES.get(
            "file"
        )

        try:
            upload = (
                BackgroundUploadService
                .store_bank_statement(
                    organization=(
                        request.api_organization
                    ),
                    uploaded_by=(
                        request.api_user
                    ),
                    uploaded_file=(
                        uploaded_file
                    ),
                )
            )

            job = (
                BackgroundJobService
                .create_job(
                    organization=(
                        request.api_organization
                    ),
                    created_by=(
                        request.api_user
                    ),
                    job_type=(
                        "BANK_STATEMENT_IMPORT"
                    ),
                    payload={
                        "upload_id":
                            str(upload.id),

                        "bank_account_id":
                            request.POST.get(
                                "bank_account_id"
                            ),

                        "statement_start_date":
                            request.POST.get(
                                "statement_start_date"
                            ),

                        "statement_end_date":
                            request.POST.get(
                                "statement_end_date"
                            ),

                        "opening_balance":
                            request.POST.get(
                                "opening_balance"
                            ),

                        "closing_balance":
                            request.POST.get(
                                "closing_balance"
                            ),
                    },
                    idempotency_key=(
                        "BANK_STATEMENT_IMPORT:"
                        f"{upload.id}"
                    ),
                )
            )

        except ValueError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=str(exc),
                    details={
                        "file": [
                            str(exc),
                        ],
                    },
                    request=request,
                )
            )

        return APIResponseService.success(
            data={
                "job": {
                    "id":
                        str(job.id),

                    "job_type":
                        job.job_type,

                    "status":
                        job.status,

                    "attempts":
                        job.attempts,

                    "max_attempts":
                        job.max_attempts,

                    "created_at": (
                        job.created_at
                        .isoformat()
                        if job.created_at
                        else None
                    ),
                },
            },
            message=(
                "Bank statement import "
                "queued successfully."
            ),
            status=202,
            request=request,
        )

    return APIResponseService.method_not_allowed(
        message=(
            "Use GET to list bank statements or "
            "POST to import one."
        ),
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_statements.detail",
    limit=120,
    window_seconds=60,
)
def bank_statement_detail_api(
    request,
    statement_id,
):
    if request.method != "GET":
        return APIResponseService.method_not_allowed(
            message="Use GET to retrieve a bank statement.",
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
        statement = (
            BankStatementAPIService
            .get_statement(
                organization=request.api_organization,
                statement_id=statement_id,
            )
        )

    except BankStatementAPIValidationError as exc:
        return APIResponseService.validation_error(
            message=exc.message,
            details=exc.details,
            request=request,
        )

    except LookupError:
        return APIResponseService.not_found(
            message="Bank statement not found.",
            request=request,
        )

    return APIResponseService.success(
        data={
            "bank_statement": (
                BankStatementAPISerializer
                .serialize_detail(
                    statement
                )
            ),
        },
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_statements.cancel",
    limit=60,
    window_seconds=60,
)
def bank_statement_cancel_api(
    request,
    statement_id,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message="Use POST to cancel a bank statement.",
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "bank_statements.cancel",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        statement = (
            BankStatementAPIService
            .cancel_statement(
                user=request.api_user,
                organization=request.api_organization,
                statement_id=statement_id,
            )
        )

    except BankStatementAPIValidationError as exc:
        return APIResponseService.validation_error(
            message=exc.message,
            details=exc.details,
            request=request,
        )

    except LookupError:
        return APIResponseService.not_found(
            message="Bank statement not found.",
            request=request,
        )

    except BankStatementAPIStateError as exc:
        return APIResponseService.unprocessable_entity(
            message=exc.message,
            details=exc.details,
            request=request,
        )

    except PermissionError:
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    return APIResponseService.success(
        data={
            "bank_statement": (
                BankStatementAPISerializer
                .serialize_detail(
                    statement
                )
            ),
        },
        message="Bank statement cancelled successfully.",
        request=request,
    )


def _line_action_error_response(
    request,
    exc,
):
    if isinstance(
        exc,
        BankStatementAPIValidationError,
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
            message="Bank statement not found.",
            request=request,
        )

    if isinstance(
        exc,
        BankStatementAPIStateError,
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
    scope="bank_statements.auto_match",
    limit=120,
    window_seconds=60,
)
def bank_statement_line_auto_match_api(
    request,
    statement_id,
    line_number,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message="Use POST to auto-match a statement line.",
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

    payload = {}

    if (
        "application/json"
        in (
            request.content_type
            or
            ""
        ).lower()
    ):
        payload, error_response = _json_body(
            request
        )

        if error_response:
            return error_response

        if not isinstance(payload, dict):
            return APIResponseService.validation_error(
                message="JSON body must be an object.",
                details={
                    "body": [
                        "JSON body must be an object.",
                    ],
                },
                request=request,
            )

    try:
        result = (
            BankStatementAPIService
            .auto_match_line(
                user=request.api_user,
                organization=request.api_organization,
                statement_id=statement_id,
                line_number=line_number,
                date_tolerance_days=payload.get(
                    "date_tolerance_days",
                    2,
                ),
            )
        )

    except (
        BankStatementAPIValidationError,
        BankStatementAPIStateError,
        LookupError,
        PermissionError,
    ) as exc:
        return _line_action_error_response(
            request,
            exc,
        )

    transaction = result.get(
        "transaction"
    )

    return APIResponseService.success(
        data={
            "statement": (
                BankStatementAPISerializer
                .serialize_summary(
                    result["statement"]
                )
            ),
            "line": (
                BankStatementAPISerializer
                .serialize_line(
                    result["line"]
                )
            ),
            "match_type": result.get("match_type"),
            "matched": bool(result.get("matched", False)),
            "candidate_count": result.get("candidate_count"),
            "transaction": (
                BankTransactionAPISerializer
                .serialize_detail(
                    transaction
                )
                if transaction
                else None
            ),
        },
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_statements.manual_match",
    limit=120,
    window_seconds=60,
)
def bank_statement_line_match_api(
    request,
    statement_id,
    line_number,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message="Use POST to match a statement line.",
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

    payload, error_response = _json_body(
        request
    )

    if error_response:
        return error_response

    if not isinstance(payload, dict):
        return APIResponseService.validation_error(
            message="JSON body must be an object.",
            details={
                "body": [
                    "JSON body must be an object.",
                ],
            },
            request=request,
        )

    try:
        result = (
            BankStatementAPIService
            .match_line(
                user=request.api_user,
                organization=request.api_organization,
                statement_id=statement_id,
                line_number=line_number,
                transaction_id=payload.get(
                    "transaction_id"
                ),
            )
        )

    except (
        BankStatementAPIValidationError,
        BankStatementAPIStateError,
        LookupError,
        PermissionError,
    ) as exc:
        return _line_action_error_response(
            request,
            exc,
        )

    return APIResponseService.success(
        data={
            "statement": (
                BankStatementAPISerializer
                .serialize_summary(
                    result["statement"]
                )
            ),
            "line": (
                BankStatementAPISerializer
                .serialize_line(
                    result["line"]
                )
            ),
            "transaction": (
                BankTransactionAPISerializer
                .serialize_detail(
                    result["transaction"]
                )
            ),
        },
        message="Statement line matched successfully.",
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="bank_statements.ignore_line",
    limit=120,
    window_seconds=60,
)
def bank_statement_line_ignore_api(
    request,
    statement_id,
    line_number,
):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message="Use POST to ignore a statement line.",
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
            BankStatementAPIService
            .ignore_line(
                user=request.api_user,
                organization=request.api_organization,
                statement_id=statement_id,
                line_number=line_number,
            )
        )

    except (
        BankStatementAPIValidationError,
        BankStatementAPIStateError,
        LookupError,
        PermissionError,
    ) as exc:
        return _line_action_error_response(
            request,
            exc,
        )

    return APIResponseService.success(
        data={
            "statement": (
                BankStatementAPISerializer
                .serialize_summary(
                    result["statement"]
                )
            ),
            "line": (
                BankStatementAPISerializer
                .serialize_line(
                    result["line"]
                )
            ),
        },
        message="Statement line ignored successfully.",
        request=request,
    )
