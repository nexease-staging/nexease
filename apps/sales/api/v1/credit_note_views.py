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
from apps.sales.api.v1.serializers import (
    CreditNoteAPISerializer,
)
from apps.sales.repositories.credit_note_repository import (
    CreditNoteRepository,
)
from apps.sales.services.credit_note_api_service import (
    CreditNoteAPIService,
    CreditNoteAPIStateError,
    CreditNoteAPIValidationError,
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
    scope="credit_notes.collection",
    limit=120,
    window_seconds=60,
)
def credit_note_collection_api(
    request,
):
    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "credit_notes.read",
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
            CreditNoteRepository
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
                        "customer_id": {
                            "field":
                                "customer",
                            "parser":
                                "object_id",
                        },
                        "invoice_id": {
                            "field":
                                "invoice",
                            "parser":
                                "object_id",
                        },
                        "sales_return_id": {
                            "field":
                                "sales_return",
                            "parser":
                                "object_id",
                        },
                        "status": {
                            "field":
                                "status",
                            "parser":
                                "string",
                        },
                    },
                    search_fields=[
                        "credit_note_number",
                        "reason",
                        "notes",
                    ],
                    allowed_sort_fields={
                        "credit_note_number":
                            "credit_note_number",
                        "credit_note_date":
                            "credit_note_date",
                        "status":
                            "status",
                        "total_amount":
                            "total_amount",
                        "applied_amount":
                            "applied_amount",
                        "remaining_credit":
                            "remaining_credit",
                        "created_at":
                            "created_at",
                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "-credit_note_date",
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
                    "credit_notes": (
                        CreditNoteAPISerializer
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
                "credit_notes.create",
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
            credit_note = (
                CreditNoteAPIService
                .create_credit_note(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except CreditNoteAPIValidationError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except CreditNoteAPIStateError as exc:
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
                    "credit_note": (
                        CreditNoteAPISerializer
                        .serialize_detail(
                            credit_note
                        )
                    ),
                },
                message=(
                    "Credit note created "
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
                "Use GET to list credit notes "
                "or POST to create one."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="credit_notes.detail",
    limit=120,
    window_seconds=60,
)
def credit_note_detail_api(
    request,
    credit_note_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve a "
                    "credit note."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "credit_notes.read",
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
        credit_note = (
            CreditNoteAPIService
            .get_credit_note(
                organization=(
                    request.api_organization
                ),
                credit_note_id=(
                    credit_note_id
                ),
            )
        )

    except CreditNoteAPIValidationError as exc:
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
                    "Credit note not found."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "credit_note": (
                    CreditNoteAPISerializer
                    .serialize_detail(
                        credit_note
                    )
                ),
            },
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="credit_notes.issue",
    limit=60,
    window_seconds=60,
)
def credit_note_issue_api(
    request,
    credit_note_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to issue a "
                    "credit note."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "credit_notes.issue",
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
        credit_note = (
            CreditNoteAPIService
            .issue_credit_note(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                credit_note_id=(
                    credit_note_id
                ),
            )
        )

    except CreditNoteAPIValidationError as exc:
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
                    "Credit note not found."
                ),
                request=request,
            )
        )

    except CreditNoteAPIStateError as exc:
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
                "credit_note": (
                    CreditNoteAPISerializer
                    .serialize_detail(
                        credit_note
                    )
                ),
            },
            message=(
                "Credit note issued "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="credit_notes.cancel",
    limit=60,
    window_seconds=60,
)
def credit_note_cancel_api(
    request,
    credit_note_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to cancel a "
                    "credit note."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "credit_notes.cancel",
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
        credit_note = (
            CreditNoteAPIService
            .cancel_credit_note(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                credit_note_id=(
                    credit_note_id
                ),
            )
        )

    except CreditNoteAPIValidationError as exc:
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
                    "Credit note not found."
                ),
                request=request,
            )
        )

    except CreditNoteAPIStateError as exc:
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
                "credit_note": (
                    CreditNoteAPISerializer
                    .serialize_detail(
                        credit_note
                    )
                ),
            },
            message=(
                "Credit note cancelled "
                "successfully."
            ),
            request=request,
        )
    )