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
    GoodsReceiptAPISerializer,
)
from apps.purchasing.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)
from apps.purchasing.services.goods_receipt_api_service import (
    GoodsReceiptAPIService,
    GoodsReceiptAPIValidationError,
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
    scope="goods_receipts.collection",
    limit=120,
    window_seconds=60,
)
def goods_receipt_collection_api(
    request,
):
    if request.method == "GET":

        if not AuthorizationService.has_permission(
            request.api_user,
            "goods_receipts.read",
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        queryset = (
            GoodsReceiptRepository
            .list_by_organization(
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
                    allowed_filters={},
                    search_fields=[
                        "grn_number",
                    ],
                    allowed_sort_fields={
                        "grn_number":
                            "grn_number",
                        "received_at":
                            "received_at",
                        "created_at":
                            "created_at",
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
                    "goods_receipts": (
                        GoodsReceiptAPISerializer
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
                message=(
                    "Goods receipts retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    if request.method == "POST":

        if not AuthorizationService.has_permission(
            request.api_user,
            "goods_receipts.create",
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        payload, error_response = (
            _json_body(request)
        )

        if error_response:
            return error_response

        try:
            goods_receipt = (
                GoodsReceiptAPIService
                .receive_goods(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except GoodsReceiptAPIValidationError as exc:
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
                    message=str(exc),
                    request=request,
                )
            )

        except PermissionError as exc:
            return (
                APIResponseService
                .forbidden(
                    message=str(exc),
                    request=request,
                )
            )

        except ValueError as exc:
            return (
                APIResponseService
                .unprocessable_entity(
                    message=str(exc),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "goods_receipt": (
                        GoodsReceiptAPISerializer
                        .serialize_detail(
                            goods_receipt
                        )
                    ),
                },
                message=(
                    "Goods receipt created "
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
                "Use GET or POST for goods receipts."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="goods_receipts.detail",
    limit=120,
    window_seconds=60,
)
def goods_receipt_detail_api(
    request,
    goods_receipt_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "a goods receipt."
                ),
                request=request,
            )
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "goods_receipts.read",
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        goods_receipt = (
            GoodsReceiptAPIService
            .get_goods_receipt(
                organization=(
                    request.api_organization
                ),
                goods_receipt_id=(
                    goods_receipt_id
                ),
            )
        )

    except GoodsReceiptAPIValidationError as exc:
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
                message="Goods receipt not found.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "goods_receipt": (
                    GoodsReceiptAPISerializer
                    .serialize_detail(
                        goods_receipt
                    )
                ),
            },
            message=(
                "Goods receipt retrieved "
                "successfully."
            ),
            request=request,
        )
    )