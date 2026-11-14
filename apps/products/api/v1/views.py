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
from apps.products.api.v1.serializers import (
    CategoryAPISerializer,
    ProductAPISerializer,
)
from apps.products.repositories.category_repository import (
    CategoryRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.products.services.product_api_service import (
    ProductAPIService,
    ProductAPIValidationError,
)
from apps.products.services.category_api_service import (
    CategoryAPIService,
    CategoryAPIValidationError,
)

from django.views.decorators.http import require_http_methods
from apps.business.models import BusinessRecord
from apps.products.models import Product


@api_login_required
@require_http_methods(["GET", "POST"])
def product_units(request):
    org = request.api_organization
    permission = "products.create" if request.method == "POST" else "products.read"
    if not AuthorizationService.has_permission(request.api_user, permission):
        return APIResponseService.forbidden(message="Permission denied.", request=request)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return APIResponseService.bad_request(message="Invalid JSON.", request=request)
        name = data.get("name") if isinstance(data, dict) else None
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 30:
            return APIResponseService.validation_error(message="Enter a unit of 1 to 30 characters.", request=request)
        name = name.strip()
        BusinessRecord.objects(organization=org, kind="product_unit", key=name.casefold()).update_one(
            upsert=True, set_on_insert__data={"name": name}, set_on_insert__created_by=request.api_user,
        )
        return APIResponseService.success(data={"unit": name}, request=request)
    names = Product.objects(organization=org).distinct("unit")
    names.extend(r.data["name"] for r in BusinessRecord.objects(organization=org, kind="product_unit").only("data"))
    units = {name.casefold(): name for name in names if name}
    return APIResponseService.success(data={"units": [units[key] for key in sorted(units)]}, request=request)


@api_login_required
@api_rate_limit(
    scope="categories.collection",
    limit=120,
    window_seconds=60,
)
def category_collection_api(
    request,
):
    # ==================================================
    # GET: LIST ACTIVE CATEGORIES
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "products.read",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        categories = (
            CategoryRepository
            .list_active(
                organization=(
                    request.api_organization
                ),
            )
        )

        serialized_categories = [
            (
                CategoryAPISerializer
                .serialize_summary(
                    category
                )
            )
            for category
            in categories
        ]

        return (
            APIResponseService
            .success(
                data={
                    "categories":
                        serialized_categories,
                    "count":
                        len(
                            serialized_categories
                        ),
                },
                message=(
                    "Product categories retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: CREATE CATEGORY
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "products.create",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

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
                APIResponseService
                .bad_request(
                    message=(
                        "Content-Type must be "
                        "application/json."
                    ),
                    request=request,
                )
            )

        try:

            payload = json.loads(
                request.body.decode(
                    "utf-8"
                )
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):

            return (
                APIResponseService
                .bad_request(
                    message="Invalid JSON body.",
                    request=request,
                )
            )

        try:

            category = (
                CategoryAPIService
                .create_category(
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except CategoryAPIValidationError as exc:

            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "category": (
                        CategoryAPISerializer
                        .serialize_detail(
                            category
                        )
                    ),
                },
                message=(
                    "Product category created "
                    "successfully."
                ),
                status=201,
                request=request,
            )
        )

    # ==================================================
    # UNSUPPORTED METHOD
    # ==================================================

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET or POST for "
                "the category collection."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="categories.detail",
    limit=120,
    window_seconds=60,
)
def category_detail_api(request, category_id):
    if request.method == "GET":
        if not AuthorizationService.has_permission(
            request.api_user,
            "products.read",
        ):
            return APIResponseService.forbidden(
                message="Permission denied.",
                request=request,
            )

        try:
            category = CategoryAPIService.get_category(
                organization=request.api_organization,
                category_id=category_id,
            )
        except LookupError:
            return APIResponseService.not_found(
                message="Category not found.",
                request=request,
            )

        return APIResponseService.success(
            data={
                "category": CategoryAPISerializer.serialize_detail(
                    category
                ),
            },
            message="Product category retrieved successfully.",
            request=request,
        )

    if request.method == "PATCH":
        if not AuthorizationService.has_permission(
            request.api_user,
            "products.update",
        ):
            return APIResponseService.forbidden(
                message="Permission denied.",
                request=request,
            )

        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return APIResponseService.validation_error(
                message="Invalid JSON body.",
                details={
                    "payload": ["Request body must contain valid JSON."]
                },
                request=request,
            )

        try:
            category = CategoryAPIService.update_category(
                organization=request.api_organization,
                category_id=category_id,
                payload=payload,
            )
        except CategoryAPIValidationError as exc:
            return APIResponseService.validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        except LookupError:
            return APIResponseService.not_found(
                message="Category not found.",
                request=request,
            )

        return APIResponseService.success(
            data={
                "category": CategoryAPISerializer.serialize_detail(
                    category
                ),
            },
            message="Product category updated successfully.",
            request=request,
        )

    return APIResponseService.method_not_allowed(
        message="Use GET or PATCH for a product category.",
        request=request,
    )

@api_login_required
@api_rate_limit(
    scope="categories.activate",
    limit=120,
    window_seconds=60,
)
def category_activate_api(request, category_id):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message="Use POST to activate a product category.",
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "products.update",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        category = CategoryAPIService.activate_category(
            organization=request.api_organization,
            category_id=category_id,
        )
    except LookupError:
        return APIResponseService.not_found(
            message="Category not found.",
            request=request,
        )

    return APIResponseService.success(
        data={
            "category": CategoryAPISerializer.serialize_detail(
                category
            ),
        },
        message="Product category activated successfully.",
        request=request,
    )


@api_login_required
@api_rate_limit(
    scope="categories.deactivate",
    limit=120,
    window_seconds=60,
)
def category_deactivate_api(request, category_id):
    if request.method != "POST":
        return APIResponseService.method_not_allowed(
            message="Use POST to deactivate a product category.",
            request=request,
        )

    if not AuthorizationService.has_permission(
        request.api_user,
        "products.delete",
    ):
        return APIResponseService.forbidden(
            message="Permission denied.",
            request=request,
        )

    try:
        category = CategoryAPIService.deactivate_category(
            organization=request.api_organization,
            category_id=category_id,
        )
    except LookupError:
        return APIResponseService.not_found(
            message="Category not found.",
            request=request,
        )

    return APIResponseService.success(
        data={
            "category": CategoryAPISerializer.serialize_detail(
                category
            ),
        },
        message="Product category deactivated successfully.",
        request=request,
    )

@api_login_required
@api_rate_limit(
    scope="products.collection",
    limit=120,
    window_seconds=60,
)
def product_collection_api(
    request,
):
    # ==================================================
    # GET: LIST PRODUCTS
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "products.read",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        # ==============================================
        # TRUSTED TENANT-SCOPED QUERYSET
        # ==============================================

        queryset = (
            ProductRepository
            .queryset_for_organization(
                organization=(
                    request.api_organization
                ),
            )
        )

        # ==============================================
        # FILTER, SEARCH, SORT AND PAGINATE
        # ==============================================

        try:

            pipeline_result = (
                APIQueryPipelineService
                .execute(
                    queryset,
                    request,
                    allowed_filters={
                        "is_active": {
                            "field":
                                "is_active",

                            "parser":
                                "boolean",
                        },
                    },
                    search_fields=[
                        "sku",
                        "name",
                        "brand",
                        "barcode",
                    ],
                    allowed_sort_fields={
                        "sku":
                            "sku",

                        "name":
                            "name",

                        "brand":
                            "brand",

                        "unit":
                            "unit",

                        "cost_price":
                            "cost_price",

                        "selling_price":
                            "selling_price",

                        "created_at":
                            "created_at",

                        "updated_at":
                            "updated_at",
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

        # ==============================================
        # SERIALIZE
        # ==============================================

        serialized_products = (
            ProductAPISerializer
            .serialize_many(
                pipeline_result[
                    "items"
                ]
            )
        )

        # ==============================================
        # RESPONSE
        # ==============================================

        return (
            APIResponseService
            .success(
                data={
                    "products":
                        serialized_products,

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
                    "Products retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: CREATE PRODUCT
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "products.create",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

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
                APIResponseService
                .bad_request(
                    message=(
                        "Content-Type must be "
                        "application/json."
                    ),
                    request=request,
                )
            )

        try:

            payload = json.loads(
                request.body.decode(
                    "utf-8"
                )
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):

            return (
                APIResponseService
                .bad_request(
                    message="Invalid JSON body.",
                    request=request,
                )
            )

        try:

            product = (
                ProductAPIService
                .create_product(
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except ProductAPIValidationError as exc:

            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except PermissionError as exc:

            return (
                APIResponseService
                .forbidden(
                    message=str(
                        exc
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "product": (
                        ProductAPISerializer
                        .serialize_detail(
                            product
                        )
                    ),
                },
                message=(
                    "Product created "
                    "successfully."
                ),
                status=201,
                request=request,
            )
        )

    # ==================================================
    # UNSUPPORTED METHOD
    # ==================================================

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET or POST for "
                "the product collection."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="products.detail",
    limit=120,
    window_seconds=60,
)
def product_detail_api(
    request,
    product_id,
):
    # ==================================================
    # GET: PRODUCT DETAIL
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "products.read",
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

            product = (
                ProductAPIService
                .get_product(
                    organization=(
                        request.api_organization
                    ),
                    product_id=product_id,
                )
            )

        except LookupError:

            return (
                APIResponseService
                .not_found(
                    message="Product not found.",
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "product": (
                        ProductAPISerializer
                        .serialize_detail(
                            product
                        )
                    ),
                },
                message=(
                    "Product retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # PATCH: UPDATE PRODUCT
    # ==================================================

    if request.method == "PATCH":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "products.update",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

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
                APIResponseService
                .bad_request(
                    message=(
                        "Content-Type must be "
                        "application/json."
                    ),
                    request=request,
                )
            )

        try:

            payload = json.loads(
                request.body.decode(
                    "utf-8"
                )
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):

            return (
                APIResponseService
                .bad_request(
                    message="Invalid JSON body.",
                    request=request,
                )
            )

        try:

            product = (
                ProductAPIService
                .update_product(
                    organization=(
                        request.api_organization
                    ),
                    product_id=product_id,
                    payload=payload,
                )
            )

        except ProductAPIValidationError as exc:

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
                    message="Product not found.",
                    request=request,
                )
            )

        except PermissionError as exc:

            return (
                APIResponseService
                .forbidden(
                    message=str(
                        exc
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "product": (
                        ProductAPISerializer
                        .serialize_detail(
                            product
                        )
                    ),
                },
                message=(
                    "Product updated "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # UNSUPPORTED METHOD
    # ==================================================

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET or PATCH for "
                "product detail."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="products.activate",
    limit=60,
    window_seconds=60,
)
def product_activate_api(
    request,
    product_id,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to activate "
                    "a product."
                ),
                request=request,
            )
        )

    # ==================================================
    # AUTHORIZATION
    # ==================================================

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "products.update",
        )
    ):

        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    # ==================================================
    # ACTIVATE
    # ==================================================

    try:

        product = (
            ProductAPIService
            .activate_product(
                organization=(
                    request.api_organization
                ),
                product_id=product_id,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message="Product not found.",
                request=request,
            )
        )

    except PermissionError as exc:

        return (
            APIResponseService
            .forbidden(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "product": (
                    ProductAPISerializer
                    .serialize_detail(
                        product
                    )
                ),
            },
            message=(
                "Product activated "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="products.deactivate",
    limit=60,
    window_seconds=60,
)
def product_deactivate_api(
    request,
    product_id,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to deactivate "
                    "a product."
                ),
                request=request,
            )
        )

    # ==================================================
    # AUTHORIZATION
    # ==================================================

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "products.delete",
        )
    ):

        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    # ==================================================
    # DEACTIVATE
    # ==================================================

    try:

        product = (
            ProductAPIService
            .deactivate_product(
                organization=(
                    request.api_organization
                ),
                product_id=product_id,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message="Product not found.",
                request=request,
            )
        )

    except PermissionError as exc:

        return (
            APIResponseService
            .forbidden(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "product": (
                    ProductAPISerializer
                    .serialize_detail(
                        product
                    )
                ),
            },
            message=(
                "Product deactivated "
                "successfully."
            ),
            request=request,
        )
    )