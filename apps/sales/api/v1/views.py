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
    AccountsReceivableAPISerializer,
    BankAccountLookupAPISerializer,
    CustomerAPISerializer,
    CustomerPaymentAPISerializer,
    InvoiceAPISerializer,
    SalesOrderAPISerializer,
)
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.sales.repositories.payment_repository import (
    PaymentRepository,
)
from apps.sales.services.invoice_api_service import (
    InvoiceAPIService,
    InvoiceAPIStateError,
    InvoiceAPIValidationError,
)
from apps.sales.services.customer_payment_api_service import (
    CustomerPaymentAPIService,
    CustomerPaymentAPIValidationError,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.services.sales_order_api_service import (
    SalesOrderAPIService,
    SalesOrderAPIStateError,
    SalesOrderAPIValidationError,
)
from apps.sales.repositories.customer_repository import (
    CustomerRepository,
)
from apps.sales.services.customer_api_service import (
    CustomerAPIService,
    CustomerAPIStateError,
    CustomerAPIValidationError,
)


@api_login_required
@api_rate_limit(
    scope="customers.collection",
    limit=120,
    window_seconds=60,
)
def customer_collection_api(
    request,
):
    # ==================================================
    # GET: LIST CUSTOMERS
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "customers.read",
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
            CustomerRepository
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
                        "is_active": {
                            "field":
                                "is_active",
                            "parser":
                                "boolean",
                        },
                    },
                    search_fields=[
                        "code",
                        "name",
                        "email",
                        "phone",
                        "gstin",
                        "city",
                        "state",
                    ],
                    allowed_sort_fields={
                        "code":
                            "code",
                        "name":
                            "name",
                        "email":
                            "email",
                        "city":
                            "city",
                        "state":
                            "state",
                        "country":
                            "country",
                        "created_at":
                            "created_at",
                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "name",
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

        serialized_customers = (
            CustomerAPISerializer
            .serialize_many(
                pipeline_result[
                    "items"
                ]
            )
        )

        return (
            APIResponseService
            .success(
                data={
                    "customers":
                        serialized_customers,
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
                    "Customers retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: CREATE CUSTOMER
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "customers.create",
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

            customer = (
                CustomerAPIService
                .create_customer(
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except CustomerAPIValidationError as exc:

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
                    "customer": (
                        CustomerAPISerializer
                        .serialize_detail(
                            customer
                        )
                    ),
                },
                message=(
                    "Customer created "
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
                "Use GET or POST for "
                "the customer collection."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="customers.detail",
    limit=120,
    window_seconds=60,
)
def customer_detail_api(
    request,
    customer_id,
):
    # ==================================================
    # GET: CUSTOMER DETAIL
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "customers.read",
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

            customer = (
                CustomerAPIService
                .get_customer(
                    organization=(
                        request.api_organization
                    ),
                    customer_id=customer_id,
                )
            )

        except CustomerAPIValidationError as exc:

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
                    message="Customer not found.",
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
                    "customer": (
                        CustomerAPISerializer
                        .serialize_detail(
                            customer
                        )
                    ),
                },
                message=(
                    "Customer retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # PATCH: UPDATE CUSTOMER
    # ==================================================

    if request.method == "PATCH":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "customers.update",
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

            customer = (
                CustomerAPIService
                .update_customer(
                    organization=(
                        request.api_organization
                    ),
                    customer_id=customer_id,
                    payload=payload,
                )
            )

        except CustomerAPIValidationError as exc:

            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except CustomerAPIStateError as exc:

            return (
                APIResponseService
                .unprocessable_entity(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except LookupError:

            return (
                APIResponseService
                .not_found(
                    message="Customer not found.",
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
                    "customer": (
                        CustomerAPISerializer
                        .serialize_detail(
                            customer
                        )
                    ),
                },
                message=(
                    "Customer updated "
                    "successfully."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET or PATCH for "
                "customer detail."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="customers.activate",
    limit=60,
    window_seconds=60,
)
def customer_activate_api(
    request,
    customer_id,
):
    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to activate "
                    "a customer."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "customers.update",
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

        customer = (
            CustomerAPIService
            .activate_customer(
                organization=(
                    request.api_organization
                ),
                customer_id=customer_id,
            )
        )

    except CustomerAPIValidationError as exc:

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
                message="Customer not found.",
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
                "customer": (
                    CustomerAPISerializer
                    .serialize_detail(
                        customer
                    )
                ),
            },
            message=(
                "Customer activated "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="customers.deactivate",
    limit=60,
    window_seconds=60,
)
def customer_deactivate_api(
    request,
    customer_id,
):
    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to deactivate "
                    "a customer."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "customers.update",
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

        customer = (
            CustomerAPIService
            .deactivate_customer(
                organization=(
                    request.api_organization
                ),
                customer_id=customer_id,
            )
        )

    except CustomerAPIValidationError as exc:

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
                message="Customer not found.",
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
                "customer": (
                    CustomerAPISerializer
                    .serialize_detail(
                        customer
                    )
                ),
            },
            message=(
                "Customer deactivated "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="sales_orders.collection",
    limit=120,
    window_seconds=60,
)
def sales_order_collection_api(
    request,
):
    # ==================================================
    # GET: LIST SALES ORDERS
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "sales_orders.read",
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
            SalesOrderRepository
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
                        "warehouse_id": {
                            "field":
                                "warehouse",
                            "parser":
                                "object_id",
                        },
                        "status": {
                            "field":
                                "status",
                        },
                    },
                    search_fields=[
                        "so_number",
                        "customer__code",
                        "customer__name",
                        "warehouse__code",
                        "warehouse__name",
                        "notes",
                    ],
                    allowed_sort_fields={
                        "so_number":
                            "so_number",
                        "status":
                            "status",
                        "order_date":
                            "order_date",
                        "expected_delivery_date": (
                            "expected_delivery_date"
                        ),
                        "subtotal":
                            "subtotal",
                        "tax_amount":
                            "tax_amount",
                        "discount_amount":
                            "discount_amount",
                        "total_amount":
                            "total_amount",
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

        return (
            APIResponseService
            .success(
                data={
                    "sales_orders": (
                        SalesOrderAPISerializer
                        .serialize_many(
                            pipeline_result[
                                "items"
                            ]
                        )
                    ),
                    "pagination": (
                        pipeline_result[
                            "pagination"
                        ]
                    ),
                    "query": (
                        pipeline_result[
                            "query"
                        ]
                    ),
                },
                message=(
                    "Sales orders retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: CREATE SALES ORDER
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "sales_orders.create",
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
                )
            )

        try:
            payload = json.loads(
                request.body
                or
                b"{}"
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return (
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
                )
            )

        try:
            sales_order = (
                SalesOrderAPIService
                .create_sales_order(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except SalesOrderAPIValidationError as exc:
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
                    "sales_order": (
                        SalesOrderAPISerializer
                        .serialize_detail(
                            sales_order
                        )
                    ),
                },
                message=(
                    "Sales order created "
                    "successfully."
                ),
                status=201,
                request=request,
            )
        )

    # ==================================================
    # METHOD RESTRICTION
    # ==================================================

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET to list or POST "
                "to create sales orders."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="sales_orders.detail",
    limit=120,
    window_seconds=60,
)
def sales_order_detail_api(
    request,
    sales_order_id,
):
    # ==================================================
    # GET: SALES ORDER DETAIL
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "sales_orders.read",
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
            sales_order = (
                SalesOrderAPIService
                .get_sales_order(
                    organization=(
                        request.api_organization
                    ),
                    sales_order_id=(
                        sales_order_id
                    ),
                )
            )

        except SalesOrderAPIValidationError as exc:
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
                        "Sales order not found."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "sales_order": (
                        SalesOrderAPISerializer
                        .serialize_detail(
                            sales_order
                        )
                    ),
                },
                message=(
                    "Sales order retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # PUT: UPDATE DRAFT SALES ORDER
    # ==================================================

    if request.method == "PUT":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "sales_orders.update",
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
                )
            )

        try:
            payload = json.loads(
                request.body
                or
                b"{}"
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return (
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
                )
            )

        try:
            sales_order = (
                SalesOrderAPIService
                .update_sales_order(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    sales_order_id=(
                        sales_order_id
                    ),
                    payload=payload,
                )
            )

        except SalesOrderAPIValidationError as exc:
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
                        "Sales order not found."
                    ),
                    request=request,
                )
            )

        except SalesOrderAPIStateError as exc:
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
                    "sales_order": (
                        SalesOrderAPISerializer
                        .serialize_detail(
                            sales_order
                        )
                    ),
                },
                message=(
                    "Sales order updated "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # METHOD RESTRICTION
    # ==================================================

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET to retrieve or PUT "
                "to update a sales order."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="sales_orders.confirm",
    limit=60,
    window_seconds=60,
)
def sales_order_confirm_api(
    request,
    sales_order_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to confirm "
                    "a sales order."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "sales_orders.update",
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
        sales_order = (
            SalesOrderAPIService
            .confirm_sales_order(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                sales_order_id=(
                    sales_order_id
                ),
            )
        )

    except SalesOrderAPIValidationError as exc:
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
                    "Sales order not found."
                ),
                request=request,
            )
        )

    except SalesOrderAPIStateError as exc:
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
                "sales_order": (
                    SalesOrderAPISerializer
                    .serialize_detail(
                        sales_order
                    )
                ),
            },
            message=(
                "Sales order confirmed "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="sales_orders.cancel",
    limit=60,
    window_seconds=60,
)
def sales_order_cancel_api(
    request,
    sales_order_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to cancel "
                    "a sales order."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "sales_orders.cancel",
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
        sales_order = (
            SalesOrderAPIService
            .cancel_sales_order(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                sales_order_id=(
                    sales_order_id
                ),
            )
        )

    except SalesOrderAPIValidationError as exc:
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
                    "Sales order not found."
                ),
                request=request,
            )
        )

    except SalesOrderAPIStateError as exc:
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
                "sales_order": (
                    SalesOrderAPISerializer
                    .serialize_detail(
                        sales_order
                    )
                ),
            },
            message=(
                "Sales order cancelled "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="sales_orders.fulfill",
    limit=60,
    window_seconds=60,
)
def sales_order_fulfill_api(
    request,
    sales_order_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to fulfil "
                    "a sales order."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "sales_orders.fulfill",
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
            )
        )

    try:
        payload = json.loads(
            request.body
            or
            b"{}"
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return (
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
            )
        )

    try:
        sales_order = (
            SalesOrderAPIService
            .fulfill_sales_order(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                sales_order_id=(
                    sales_order_id
                ),
                payload=payload,
            )
        )

    except SalesOrderAPIValidationError as exc:
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
                    "Sales order not found."
                ),
                request=request,
            )
        )

    except SalesOrderAPIStateError as exc:
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
                "sales_order": (
                    SalesOrderAPISerializer
                    .serialize_detail(
                        sales_order
                    )
                ),
            },
            message=(
                "Sales order fulfilled "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="invoice_bank_accounts.list",
    limit=120,
    window_seconds=60,
)
def invoice_bank_account_list_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to list active "
                    "payment accounts."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "invoices.record_payment",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    bank_accounts = (
        InvoiceAPIService
        .list_active_bank_accounts(
            organization=(
                request.api_organization
            ),
        )
    )

    serialized_bank_accounts = (
        BankAccountLookupAPISerializer
        .serialize_many(
            bank_accounts
        )
    )

    return (
        APIResponseService
        .success(
            data={
                "bank_accounts": (
                    serialized_bank_accounts
                ),
                "count":
                    len(
                        serialized_bank_accounts
                    ),
            },
            message=(
                "Payment accounts retrieved "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="invoices.collection",
    limit=120,
    window_seconds=60,
)
def invoice_collection_api(
    request,
):
    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "invoices.read",
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
            InvoiceRepository
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
                        "sales_order_id": {
                            "field":
                                "sales_order",
                            "parser":
                                "object_id",
                        },
                        "status": {
                            "field":
                                "status",
                        },
                    },
                    search_fields=[
                        "invoice_number",
                        "sales_order__so_number",
                        "customer__code",
                        "customer__name",
                        "billing_name",
                        "customer_gstin",
                        "notes",
                    ],
                    allowed_sort_fields={
                        "invoice_number":
                            "invoice_number",
                        "status":
                            "status",
                        "invoice_date":
                            "invoice_date",
                        "due_date":
                            "due_date",
                        "total_amount":
                            "total_amount",
                        "amount_paid":
                            "amount_paid",
                        "balance_due":
                            "balance_due",
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

        return (
            APIResponseService
            .success(
                data={
                    "invoices": (
                        InvoiceAPISerializer
                        .serialize_many(
                            pipeline_result[
                                "items"
                            ]
                        )
                    ),
                    "pagination": (
                        pipeline_result[
                            "pagination"
                        ]
                    ),
                    "query": (
                        pipeline_result[
                            "query"
                        ]
                    ),
                },
                message=(
                    "Invoices retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "invoices.create",
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
                )
            )

        try:
            payload = json.loads(
                request.body
                or
                b"{}"
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return (
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
                )
            )

        try:
            invoice = (
                InvoiceAPIService
                .create_invoice(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except InvoiceAPIValidationError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except InvoiceAPIStateError as exc:
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
                    "invoice": (
                        InvoiceAPISerializer
                        .serialize_detail(
                            invoice
                        )
                    ),
                },
                message=(
                    "Invoice created "
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
                "Use GET to list or POST "
                "to create invoices."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="invoices.detail",
    limit=120,
    window_seconds=60,
)
def invoice_detail_api(
    request,
    invoice_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "an invoice."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "invoices.read",
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
        invoice = (
            InvoiceAPIService
            .get_invoice(
                organization=(
                    request.api_organization
                ),
                invoice_id=invoice_id,
            )
        )

    except InvoiceAPIValidationError as exc:
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
                message="Invoice not found.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "invoice": (
                    InvoiceAPISerializer
                    .serialize_detail(
                        invoice
                    )
                ),
            },
            message=(
                "Invoice retrieved "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="invoices.issue",
    limit=60,
    window_seconds=60,
)
def invoice_issue_api(
    request,
    invoice_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to issue "
                    "an invoice."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "invoices.issue",
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
        invoice = (
            InvoiceAPIService
            .issue_invoice(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                invoice_id=invoice_id,
            )
        )

    except InvoiceAPIValidationError as exc:
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
                message="Invoice not found.",
                request=request,
            )
        )

    except InvoiceAPIStateError as exc:
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
                "invoice": (
                    InvoiceAPISerializer
                    .serialize_detail(
                        invoice
                    )
                ),
            },
            message=(
                "Invoice issued "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="invoices.cancel",
    limit=60,
    window_seconds=60,
)
def invoice_cancel_api(
    request,
    invoice_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to cancel "
                    "an invoice."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "invoices.cancel",
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
        invoice = (
            InvoiceAPIService
            .cancel_invoice(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                invoice_id=invoice_id,
            )
        )

    except InvoiceAPIValidationError as exc:
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
                message="Invoice not found.",
                request=request,
            )
        )

    except InvoiceAPIStateError as exc:
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
                "invoice": (
                    InvoiceAPISerializer
                    .serialize_detail(
                        invoice
                    )
                ),
            },
            message=(
                "Invoice cancelled "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="invoices.record_payment",
    limit=60,
    window_seconds=60,
)
def invoice_record_payment_api(
    request,
    invoice_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to record "
                    "an Invoice payment."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "invoices.record_payment",
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
            )
        )

    try:
        payload = json.loads(
            request.body
            or
            b"{}"
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return (
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
            )
        )

    try:
        result = (
            InvoiceAPIService
            .record_payment(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                invoice_id=invoice_id,
                payload=payload,
            )
        )

    except InvoiceAPIValidationError as exc:
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
                message="Invoice not found.",
                request=request,
            )
        )

    except InvoiceAPIStateError as exc:
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
                "invoice": (
                    InvoiceAPISerializer
                    .serialize_detail(
                        result["invoice"]
                    )
                ),
                "payment": (
                    CustomerPaymentAPISerializer
                    .serialize_detail(
                        result["payment"]
                    )
                ),
            },
            message=(
                "Invoice payment recorded "
                "successfully."
            ),
            status=201,
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="customer_payments.collection",
    limit=120,
    window_seconds=60,
)
def customer_payment_collection_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to list "
                    "customer payments."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "customer_payments.read",
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
        PaymentRepository
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
                            (
                                "allocations"
                                "__invoice"
                            ),
                        "parser":
                            "object_id",
                    },
                    "bank_account_id": {
                        "field":
                            "bank_account",
                        "parser":
                            "object_id",
                    },
                    "payment_method": {
                        "field":
                            "payment_method",
                    },
                },
                search_fields=[
                    "payment_number",
                    "customer__code",
                    "customer__name",
                    "reference_number",
                    "bank_account__account_name",
                    "bank_account__bank_name",
                    "notes",
                ],
                allowed_sort_fields={
                    "payment_number":
                        "payment_number",
                    "payment_date":
                        "payment_date",
                    "amount":
                        "amount",
                    "payment_method":
                        "payment_method",
                    "created_at":
                        "created_at",
                    "updated_at":
                        "updated_at",
                },
                default_sort=[
                    "-payment_date",
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
                "payments": (
                    CustomerPaymentAPISerializer
                    .serialize_many(
                        pipeline_result[
                            "items"
                        ]
                    )
                ),
                "pagination": (
                    pipeline_result[
                        "pagination"
                    ]
                ),
                "query": (
                    pipeline_result[
                        "query"
                    ]
                ),
            },
            message=(
                "Customer payments retrieved "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="customer_payments.detail",
    limit=120,
    window_seconds=60,
)
def customer_payment_detail_api(
    request,
    payment_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "a customer payment."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "customer_payments.read",
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
        payment = (
            CustomerPaymentAPIService
            .get_payment(
                organization=(
                    request.api_organization
                ),
                payment_id=payment_id,
            )
        )

    except (
        CustomerPaymentAPIValidationError
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
                    "Customer payment "
                    "not found."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "payment": (
                    CustomerPaymentAPISerializer
                    .serialize_detail(
                        payment
                    )
                ),
            },
            message=(
                "Customer payment retrieved "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="accounts_receivable.summary",
    limit=120,
    window_seconds=60,
)
def accounts_receivable_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "accounts receivable."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "invoices.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    result = (
        CustomerPaymentAPIService
        .get_receivable_summary(
            organization=(
                request.api_organization
            ),
        )
    )

    return (
        APIResponseService
        .success(
            data={
                "accounts_receivable": (
                    AccountsReceivableAPISerializer
                    .serialize_summary(
                        result
                    )
                ),
            },
            message=(
                "Accounts receivable retrieved "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="accounts_receivable.aging",
    limit=120,
    window_seconds=60,
)
def accounts_receivable_aging_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "receivable aging."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "invoices.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    result = (
        CustomerPaymentAPIService
        .get_aging_summary(
            organization=(
                request.api_organization
            ),
        )
    )

    return (
        APIResponseService
        .success(
            data={
                "aging": (
                    AccountsReceivableAPISerializer
                    .serialize_aging(
                        result
                    )
                ),
            },
            message=(
                "Receivable aging retrieved "
                "successfully."
            ),
            request=request,
        )
    )