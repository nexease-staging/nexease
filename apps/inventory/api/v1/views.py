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
from apps.inventory.api.v1.serializers import (
    InventoryAPISerializer,
    StockMovementAPISerializer,
    StockTransferAPISerializer,
    WarehouseAPISerializer,
)
from apps.inventory.repositories.stock_transfer_repository import (
    StockTransferRepository,
)
from apps.inventory.services.stock_transfer_api_service import (
    StockTransferAPIService,
    StockTransferAPIValidationError,
)
from apps.inventory.repositories.stock_movement_repository import (
    StockMovementRepository,
)
from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)
from apps.inventory.services.inventory_api_service import (
    InventoryAPIService,
    InventoryAPIValidationError,
)
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.inventory.services.warehouse_api_service import (
    WarehouseAPIService,
    WarehouseAPIValidationError,
)


@api_login_required
@api_rate_limit(
    scope="warehouses.collection",
    limit=120,
    window_seconds=60,
)
def warehouse_collection_api(
    request,
):
    # ==================================================
    # GET: LIST WAREHOUSES
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "warehouses.read",
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
            WarehouseRepository
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
                        "country": {
                            "field":
                                "country",
                            "parser":
                                "string",
                        },
                        "state": {
                            "field":
                                "state",
                            "parser":
                                "string",
                        },
                        "city": {
                            "field":
                                "city",
                            "parser":
                                "string",
                        },
                    },
                    search_fields=[
                        "code",
                        "name",
                        "address",
                        "city",
                        "state",
                        "country",
                        "pincode",
                    ],
                    allowed_sort_fields={
                        "code":
                            "code",
                        "name":
                            "name",
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
                        "-created_at",
                        "-id",
                    ],
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

        serialized_warehouses = (
            WarehouseAPISerializer
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
                    "warehouses":
                        serialized_warehouses,
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
                    "Warehouses retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: CREATE WAREHOUSE
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "warehouses.create",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        if (
            request.content_type
            !=
            "application/json"
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
                request.body
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

            warehouse = (
                WarehouseAPIService
                .create_warehouse(
                    organization=(
                        request
                        .api_organization
                    ),
                    payload=payload,
                )
            )

        except WarehouseAPIValidationError as exc:

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
                    "warehouse": (
                        WarehouseAPISerializer
                        .serialize_detail(
                            warehouse
                        )
                    ),
                },
                message=(
                    "Warehouse created "
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
                "the warehouse collection."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="warehouses.detail",
    limit=120,
    window_seconds=60,
)
def warehouse_detail_api(
    request,
    warehouse_id,
):
    # ==================================================
    # GET: WAREHOUSE DETAIL
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "warehouses.read",
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

            warehouse = (
                WarehouseAPIService
                .get_warehouse(
                    organization=(
                        request
                        .api_organization
                    ),
                    warehouse_id=(
                        warehouse_id
                    ),
                )
            )

        except LookupError:

            return (
                APIResponseService
                .not_found(
                    message="Warehouse not found.",
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "warehouse": (
                        WarehouseAPISerializer
                        .serialize_detail(
                            warehouse
                        )
                    ),
                },
                message=(
                    "Warehouse retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # PATCH: UPDATE WAREHOUSE
    # ==================================================

    if request.method == "PATCH":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "warehouses.update",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        if (
            request.content_type
            !=
            "application/json"
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
                request.body
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

            warehouse = (
                WarehouseAPIService
                .update_warehouse(
                    organization=(
                        request
                        .api_organization
                    ),
                    warehouse_id=(
                        warehouse_id
                    ),
                    payload=payload,
                )
            )

        except WarehouseAPIValidationError as exc:

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
                    message="Warehouse not found.",
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
                    "warehouse": (
                        WarehouseAPISerializer
                        .serialize_detail(
                            warehouse
                        )
                    ),
                },
                message=(
                    "Warehouse updated "
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
                "warehouse detail."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="warehouses.activate",
    limit=60,
    window_seconds=60,
)
def warehouse_activate_api(
    request,
    warehouse_id,
):
    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to activate "
                    "a warehouse."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "warehouses.update",
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

        warehouse = (
            WarehouseAPIService
            .activate_warehouse(
                organization=(
                    request.api_organization
                ),
                warehouse_id=warehouse_id,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message="Warehouse not found.",
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
                "warehouse": (
                    WarehouseAPISerializer
                    .serialize_detail(
                        warehouse
                    )
                ),
            },
            message=(
                "Warehouse activated "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="warehouses.deactivate",
    limit=60,
    window_seconds=60,
)
def warehouse_deactivate_api(
    request,
    warehouse_id,
):
    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to deactivate "
                    "a warehouse."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "warehouses.update",
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

        warehouse = (
            WarehouseAPIService
            .deactivate_warehouse(
                organization=(
                    request.api_organization
                ),
                warehouse_id=warehouse_id,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message="Warehouse not found.",
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
                "warehouse": (
                    WarehouseAPISerializer
                    .serialize_detail(
                        warehouse
                    )
                ),
            },
            message=(
                "Warehouse deactivated "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="inventory.collection",
    limit=120,
    window_seconds=60,
)
def inventory_collection_api(
    request,
):
    # ==================================================
    # GET: LIST INVENTORY BALANCES
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "inventory.read",
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
            InventoryRepository
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
                        "product_id": {
                            "field":
                                "product",
                            "parser":
                                "object_id",
                        },
                        "warehouse_id": {
                            "field":
                                "warehouse",
                            "parser":
                                "object_id",
                        },
                    },
                    search_fields=[],
                    allowed_sort_fields={
                        "quantity":
                            "quantity",
                        "reserved_quantity":
                            "reserved_quantity",
                        "created_at":
                            "created_at",
                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "-updated_at",
                        "-id",
                    ],
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
                    "inventory": (
                        InventoryAPISerializer
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
                    "Inventory balances retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: CREATE OPENING INVENTORY
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "inventory.create",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        if (
            request.content_type
            !=
            "application/json"
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
                request.body
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

            inventory = (
                InventoryAPIService
                .create_inventory(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except InventoryAPIValidationError as exc:

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
                    "inventory": (
                        InventoryAPISerializer
                        .serialize_detail(
                            inventory
                        )
                    ),
                },
                message=(
                    "Opening inventory created "
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
                "the inventory collection."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="inventory.detail",
    limit=120,
    window_seconds=60,
)
def inventory_detail_api(
    request,
    inventory_id,
):
    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "an inventory balance."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "inventory.read",
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

        inventory = (
            InventoryAPIService
            .get_inventory(
                organization=(
                    request.api_organization
                ),
                inventory_id=inventory_id,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message="Inventory not found.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "inventory": (
                    InventoryAPISerializer
                    .serialize_detail(
                        inventory
                    )
                ),
            },
            message=(
                "Inventory balance retrieved "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="inventory.adjust",
    limit=60,
    window_seconds=60,
)
def inventory_adjust_api(
    request,
    inventory_id,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to adjust "
                    "inventory."
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
            "inventory.adjust",
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
    # CONTENT TYPE AND JSON
    # ==================================================

    if (
        request.content_type
        !=
        "application/json"
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
            request.body
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

    # ==================================================
    # ADJUSTMENT
    # ==================================================

    try:

        inventory = (
            InventoryAPIService
            .adjust_inventory(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                inventory_id=inventory_id,
                payload=payload,
            )
        )

    except InventoryAPIValidationError as exc:

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
                message="Inventory not found.",
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
                "inventory": (
                    InventoryAPISerializer
                    .serialize_detail(
                        inventory
                    )
                ),
            },
            message=(
                "Inventory adjusted "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="stock_movements.collection",
    limit=120,
    window_seconds=60,
)
def stock_movement_collection_api(
    request,
):
    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "stock movements."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "inventory.read",
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
        StockMovementRepository
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
                    "inventory_id": {
                        "field":
                            "inventory",
                        "parser":
                            "object_id",
                    },
                    "product_id": {
                        "field":
                            "product",
                        "parser":
                            "object_id",
                    },
                    "warehouse_id": {
                        "field":
                            "warehouse",
                        "parser":
                            "object_id",
                    },
                    "movement_type": {
                        "field":
                            "movement_type",
                        "parser":
                            "string",
                        "allowed_values": (
                            StockMovementService
                            .VALID_MOVEMENT_TYPES
                        ),
                    },
                    "reference_type": {
                        "field":
                            "reference_type",
                        "parser":
                            "string",
                    },
                    "reference_id": {
                        "field":
                            "reference_id",
                        "parser":
                            "string",
                    },
                },
                search_fields=[
                    "reference_type",
                    "reference_id",
                    "notes",
                ],
                allowed_sort_fields={
                    "movement_type":
                        "movement_type",
                    "quantity":
                        "quantity",
                    "created_at":
                        "created_at",
                },
                default_sort=[
                    "-created_at",
                    "-id",
                ],
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
                "movements": (
                    StockMovementAPISerializer
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
                "Stock movements retrieved "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="stock_movements.detail",
    limit=120,
    window_seconds=60,
)
def stock_movement_detail_api(
    request,
    movement_id,
):
    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "a stock movement."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "inventory.read",
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

        movement = (
            StockMovementService
            .get_movement(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                movement_id=movement_id,
            )
        )

    except ValueError:

        return (
            APIResponseService
            .not_found(
                message=(
                    "Stock movement not found."
                ),
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
                "movement": (
                    StockMovementAPISerializer
                    .serialize_detail(
                        movement
                    )
                ),
            },
            message=(
                "Stock movement retrieved "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="stock_transfers.collection",
    limit=120,
    window_seconds=60,
)
def stock_transfer_collection_api(
    request,
):
    # ==================================================
    # GET: LIST TRANSFERS
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "inventory.read",
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
            StockTransferRepository
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
                        "product_id": {
                            "field":
                                "product",
                            "parser":
                                "object_id",
                        },
                        "source_warehouse_id": {
                            "field":
                                "source_warehouse",
                            "parser":
                                "object_id",
                        },
                        "destination_warehouse_id": {
                            "field":
                                "destination_warehouse",
                            "parser":
                                "object_id",
                        },
                        "status": {
                            "field":
                                "status",
                            "parser":
                                "string",
                            "allowed_values": {
                                "DRAFT",
                                "COMPLETED",
                                "CANCELLED",
                            },
                        },
                    },
                    search_fields=[
                        "transfer_number",
                        "notes",
                    ],
                    allowed_sort_fields={
                        "transfer_number":
                            "transfer_number",
                        "quantity":
                            "quantity",
                        "status":
                            "status",
                        "created_at":
                            "created_at",
                        "completed_at":
                            "completed_at",
                    },
                    default_sort=[
                        "-created_at",
                        "-id",
                    ],
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
                    "transfers": (
                        StockTransferAPISerializer
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
                    "Stock transfers retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: EXECUTE TRANSFER
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "inventory.transfer",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        if (
            request.content_type
            !=
            "application/json"
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
                request.body
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

            transfer = (
                StockTransferAPIService
                .create_transfer(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except StockTransferAPIValidationError as exc:

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
                    "transfer": (
                        StockTransferAPISerializer
                        .serialize_detail(
                            transfer
                        )
                    ),
                },
                message=(
                    "Stock transferred "
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
                "stock transfers."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="stock_transfers.detail",
    limit=120,
    window_seconds=60,
)
def stock_transfer_detail_api(
    request,
    transfer_id,
):
    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "a stock transfer."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "inventory.read",
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

        transfer = (
            StockTransferAPIService
            .get_transfer(
                organization=(
                    request.api_organization
                ),
                transfer_id=transfer_id,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message=(
                    "Stock transfer not found."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "transfer": (
                    StockTransferAPISerializer
                    .serialize_detail(
                        transfer
                    )
                ),
            },
            message=(
                "Stock transfer retrieved "
                "successfully."
            ),
            request=request,
        )
    )