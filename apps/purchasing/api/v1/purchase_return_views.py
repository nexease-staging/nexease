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
from apps.purchasing.api.v1.serializers import (
    PurchaseReturnAPISerializer,
)
from apps.purchasing.repositories.purchase_return_repository import (
    PurchaseReturnRepository,
)
from apps.purchasing.services.purchase_return_api_service import (
    PurchaseReturnAPIService,
    PurchaseReturnAPIStateError,
    PurchaseReturnAPIValidationError,
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
    scope="purchase_returns.collection",
    limit=120,
    window_seconds=60,
)
def purchase_return_collection_api(
    request,
):
    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "purchase_returns.read",
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
            PurchaseReturnRepository
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
                        "supplier_id": {
                            "field":
                                "supplier",
                            "parser":
                                "object_id",
                        },
                        "purchase_order_id": {
                            "field":
                                "purchase_order",
                            "parser":
                                "object_id",
                        },
                        "vendor_bill_id": {
                            "field":
                                "vendor_bill",
                            "parser":
                                "object_id",
                        },
                        "warehouse_id": {
                            "field":
                                "warehouse",
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
                        "return_number",
                        "reason",
                        "notes",
                    ],
                    allowed_sort_fields={
                        "return_number":
                            "return_number",
                        "return_date":
                            "return_date",
                        "status":
                            "status",
                        "total_amount":
                            "total_amount",
                        "created_at":
                            "created_at",
                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "-return_date",
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
                    "purchase_returns": (
                        PurchaseReturnAPISerializer
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
                "purchase_returns.create",
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
            purchase_return = (
                PurchaseReturnAPIService
                .create_purchase_return(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except PurchaseReturnAPIValidationError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except PurchaseReturnAPIStateError as exc:
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
                    "purchase_return": (
                        PurchaseReturnAPISerializer
                        .serialize_detail(
                            purchase_return
                        )
                    ),
                },
                message=(
                    "Purchase return created "
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
                "Use GET to list purchase "
                "returns or POST to create one."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="purchase_returns.detail",
    limit=120,
    window_seconds=60,
)
def purchase_return_detail_api(
    request,
    purchase_return_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve a "
                    "purchase return."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "purchase_returns.read",
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
        purchase_return = (
            PurchaseReturnAPIService
            .get_purchase_return(
                organization=(
                    request.api_organization
                ),
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

    except PurchaseReturnAPIValidationError as exc:
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
                    "Purchase return not found."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "purchase_return": (
                    PurchaseReturnAPISerializer
                    .serialize_detail(
                        purchase_return
                    )
                ),
            },
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="purchase_returns.confirm",
    limit=60,
    window_seconds=60,
)
def purchase_return_confirm_api(
    request,
    purchase_return_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to confirm a "
                    "purchase return."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "purchase_returns.confirm",
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
        purchase_return = (
            PurchaseReturnAPIService
            .confirm_purchase_return(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

    except PurchaseReturnAPIValidationError as exc:
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
                    "Purchase return not found."
                ),
                request=request,
            )
        )

    except PurchaseReturnAPIStateError as exc:
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
                "purchase_return": (
                    PurchaseReturnAPISerializer
                    .serialize_detail(
                        purchase_return
                    )
                ),
            },
            message=(
                "Purchase return confirmed "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="purchase_returns.cancel",
    limit=60,
    window_seconds=60,
)
def purchase_return_cancel_api(
    request,
    purchase_return_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to cancel a "
                    "purchase return."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "purchase_returns.cancel",
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
        purchase_return = (
            PurchaseReturnAPIService
            .cancel_purchase_return(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

    except PurchaseReturnAPIValidationError as exc:
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
                    "Purchase return not found."
                ),
                request=request,
            )
        )

    except PurchaseReturnAPIStateError as exc:
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
                "purchase_return": (
                    PurchaseReturnAPISerializer
                    .serialize_detail(
                        purchase_return
                    )
                ),
            },
            message=(
                "Purchase return cancelled "
                "successfully."
            ),
            request=request,
        )
    )