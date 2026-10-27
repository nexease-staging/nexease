import json
from bson import ObjectId
from bson.errors import InvalidId
from django.http import JsonResponse

from apps.inventory.models import Inventory, Warehouse, StockMovement, StockTransfer
from apps.inventory.services.inventory_service import (
    InventoryService,
)
from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)
from apps.inventory.services.stock_transfer_service import (
    StockTransferService,
)
from apps.products.models import Product
from django.http import JsonResponse

from apps.inventory.services.warehouse_service import WarehouseService
from apps.inventory.repositories.stock_transfer_repository import (
    StockTransferRepository,
)

def warehouse_list(request):
    """
    List warehouses belonging to the authenticated
    user's organization.

    GET  /warehouses/
    POST /warehouses/
    """

    if request.method == "GET":
        user = request.user

        if not user.is_authenticated:
            return JsonResponse(
                {
                    "error": "Not authenticated."
                },
                status=401,
            )

        try:
            warehouses = WarehouseService.list_warehouses(
                user=user,
                organization=user.organization,
            )

        except PermissionError as e:
            return JsonResponse(
                {
                    "error": str(e)
                },
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {
                    "error": str(e)
                },
                status=400,
            )

        data = []

        for warehouse in warehouses:
            data.append(
                {
                    "id": str(warehouse.id),
                    "name": warehouse.name,
                    "code": warehouse.code,
                    "address": warehouse.address,
                    "city": warehouse.city,
                    "state": warehouse.state,
                    "country": warehouse.country,
                    "pincode": warehouse.pincode,
                    "is_active": warehouse.is_active,
                }
            )

        return JsonResponse(
            {
                "count": len(data),
                "warehouses": data,
            },
            status=200,
        )

    if request.method == "POST":
        return warehouse_create(request)

    return JsonResponse(
        {
            "error": "Method not allowed."
        },
        status=405,
    )


def warehouse_create(request):
    """
    Create a warehouse.

    POST /warehouses/
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        payload = json.loads(
            request.body
        )

        warehouse = WarehouseService.create_warehouse(
            user=user,
            organization=user.organization,
            name=payload.get("name", ""),
            code=payload.get("code", ""),
            address=payload.get("address", ""),
            city=payload.get("city", ""),
            state=payload.get("state", ""),
            country=payload.get(
                "country",
                "India",
            ),
            pincode=payload.get(
                "pincode",
                "",
            ),
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    except json.JSONDecodeError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": "Warehouse created successfully.",
            "warehouse": {
                "id": str(warehouse.id),
                "name": warehouse.name,
                "code": warehouse.code,
                "address": warehouse.address,
                "city": warehouse.city,
                "state": warehouse.state,
                "country": warehouse.country,
                "pincode": warehouse.pincode,
                "is_active": warehouse.is_active,
            },
        },
        status=201,
    )


def warehouse_detail(
    request,
    warehouse_id,
):
    """
    Retrieve or update a single warehouse.

    GET /warehouses/<warehouse_id>/
    PUT /warehouses/<warehouse_id>/
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    if request.method == "GET":

        try:
            warehouse = WarehouseService.get_warehouse(
                user=user,
                organization=user.organization,
                warehouse_id=warehouse_id,
            )

        except PermissionError as e:
            return JsonResponse(
                {
                    "error": str(e)
                },
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {
                    "error": str(e)
                },
                status=400,
            )

        return JsonResponse(
            {
                "id": str(warehouse.id),
                "name": warehouse.name,
                "code": warehouse.code,
                "address": warehouse.address,
                "city": warehouse.city,
                "state": warehouse.state,
                "country": warehouse.country,
                "pincode": warehouse.pincode,
                "is_active": warehouse.is_active,
            },
            status=200,
        )

    if request.method == "PUT":

        try:
            payload = json.loads(
                request.body
            )

            warehouse = WarehouseService.update_warehouse(
                user=user,
                organization=user.organization,
                warehouse_id=warehouse_id,
                name=payload.get(
                    "name",
                    "",
                ),
                code=payload.get(
                    "code",
                    "",
                ),
                address=payload.get(
                    "address",
                    "",
                ),
                city=payload.get(
                    "city",
                    "",
                ),
                state=payload.get(
                    "state",
                    "",
                ),
                country=payload.get(
                    "country",
                    "India",
                ),
                pincode=payload.get(
                    "pincode",
                    "",
                ),
                is_active=payload.get(
                    "is_active",
                    True,
                ),
            )

        except PermissionError as e:
            return JsonResponse(
                {
                    "error": str(e)
                },
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {
                    "error": str(e)
                },
                status=400,
            )

        except json.JSONDecodeError as e:
            return JsonResponse(
                {
                    "error": str(e)
                },
                status=400,
            )

        return JsonResponse(
            {
                "message": "Warehouse updated successfully.",
                "warehouse": {
                    "id": str(warehouse.id),
                    "name": warehouse.name,
                    "code": warehouse.code,
                    "address": warehouse.address,
                    "city": warehouse.city,
                    "state": warehouse.state,
                    "country": warehouse.country,
                    "pincode": warehouse.pincode,
                    "is_active": warehouse.is_active,
                },
            },
            status=200,
        )

    return JsonResponse(
        {
            "error": "Method not allowed."
        },
        status=405,
    )


def warehouse_activate(
    request,
    warehouse_id,
):
    """
    Activate a warehouse.

    POST /warehouses/<warehouse_id>/activate/
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        warehouse = WarehouseService.activate_warehouse(
            user=user,
            organization=user.organization,
            warehouse_id=warehouse_id,
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": "Warehouse activated successfully.",
            "warehouse": {
                "id": str(warehouse.id),
                "name": warehouse.name,
                "code": warehouse.code,
                "address": warehouse.address,
                "city": warehouse.city,
                "state": warehouse.state,
                "country": warehouse.country,
                "pincode": warehouse.pincode,
                "is_active": warehouse.is_active,
            },
        },
        status=200,
    )


def warehouse_deactivate(
    request,
    warehouse_id,
):
    """
    Deactivate a warehouse.

    POST /warehouses/<warehouse_id>/deactivate/
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        warehouse = WarehouseService.deactivate_warehouse(
            user=user,
            organization=user.organization,
            warehouse_id=warehouse_id,
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": "Warehouse deactivated successfully.",
            "warehouse": {
                "id": str(warehouse.id),
                "name": warehouse.name,
                "code": warehouse.code,
                "address": warehouse.address,
                "city": warehouse.city,
                "state": warehouse.state,
                "country": warehouse.country,
                "pincode": warehouse.pincode,
                "is_active": warehouse.is_active,
            },
        },
        status=200,
    )


def warehouse_router(request):
    """
    Route warehouse requests based on HTTP method.
    """

    if request.method == "GET":
        return warehouse_list(request)

    if request.method == "POST":
        return warehouse_create(request)

    return JsonResponse(
        {
            "error": "Method not allowed."
        },
        status=405,
    )





def _inventory_to_dict(inventory):
    """
    Convert an Inventory document into
    a JSON-serializable dictionary.
    """

    return {
        "id": str(inventory.id),
        "product": {
            "id": str(inventory.product.id),
            "sku": inventory.product.sku,
            "name": inventory.product.name,
        },
        "warehouse": {
            "id": str(inventory.warehouse.id),
            "code": inventory.warehouse.code,
            "name": inventory.warehouse.name,
        },
        "quantity": str(inventory.quantity),
        "reserved_quantity": str(
            inventory.reserved_quantity
        ),
        "available_quantity": str(
            inventory.quantity
            - inventory.reserved_quantity
        ),
        "created_at": (
            inventory.created_at.isoformat()
            if inventory.created_at
            else None
        ),
        "updated_at": (
            inventory.updated_at.isoformat()
            if inventory.updated_at
            else None
        ),
    }


def inventory_list(request):
    """
    List inventory or create inventory.
    """

    if request.method == "POST":
        return inventory_create(request)

    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        inventory = InventoryService.list_inventory(
            user=user,
            organization=user.organization,
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    data = [
        _inventory_to_dict(item)
        for item in inventory
    ]

    return JsonResponse(
        {
            "count": len(data),
            "inventory": data,
        },
        status=200,
    )


def inventory_create(request):
    """
    Create inventory for a product
    at a warehouse.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": "Invalid JSON."
            },
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "error": "JSON body must be an object."
            },
            status=400,
        )

    required_fields = [
        "product_id",
        "warehouse_id",
    ]

    missing_fields = [
        field
        for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        return JsonResponse(
            {
                "error": "Missing required fields.",
                "fields": missing_fields,
            },
            status=400,
        )

    product_id = data.get(
        "product_id"
    )

    warehouse_id = data.get(
        "warehouse_id"
    )

    try:
        ObjectId(product_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid product ID."
            },
            status=400,
        )

    try:
        ObjectId(warehouse_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid warehouse ID."
            },
            status=400,
        )

    product = Product.objects(
        id=product_id,
        organization=user.organization,
    ).first()

    if not product:
        return JsonResponse(
            {
                "error": "Product not found."
            },
            status=404,
        )

    warehouse = Warehouse.objects(
        id=warehouse_id,
        organization=user.organization,
    ).first()

    if not warehouse:
        return JsonResponse(
            {
                "error": "Warehouse not found."
            },
            status=404,
        )

    try:
        inventory = InventoryService.create_inventory(
            user=user,
            organization=user.organization,
            product=product,
            warehouse=warehouse,
            quantity=data.get(
                "quantity",
                0,
            ),
            reserved_quantity=data.get(
                "reserved_quantity",
                0,
            ),
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": "Inventory created successfully.",
            "inventory": _inventory_to_dict(
                inventory
            ),
        },
        status=201,
    )


def inventory_detail(
    request,
    inventory_id,
):
    """
    Retrieve one inventory record.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(inventory_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid inventory ID."
            },
            status=400,
        )

    try:
        inventory = InventoryService.get_inventory(
            user=user,
            organization=user.organization,
            inventory_id=inventory_id,
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=404,
        )

    return JsonResponse(
        _inventory_to_dict(inventory),
        status=200,
    )


def inventory_by_product(
    request,
    product_id,
):
    """
    Return inventory for a specific product.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(product_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid product ID."
            },
            status=400,
        )

    product = Product.objects(
        id=product_id,
        organization=user.organization,
    ).first()

    if not product:
        return JsonResponse(
            {
                "error": "Product not found."
            },
            status=404,
        )

    try:
        inventory = (
            InventoryService
            .list_inventory_by_product(
                user=user,
                organization=user.organization,
                product=product,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    data = [
        _inventory_to_dict(item)
        for item in inventory
    ]

    return JsonResponse(
        {
            "count": len(data),
            "inventory": data,
        },
        status=200,
    )


def inventory_by_warehouse(
    request,
    warehouse_id,
):
    """
    Return inventory for a specific warehouse.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(warehouse_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid warehouse ID."
            },
            status=400,
        )

    warehouse = Warehouse.objects(
        id=warehouse_id,
        organization=user.organization,
    ).first()

    if not warehouse:
        return JsonResponse(
            {
                "error": "Warehouse not found."
            },
            status=404,
        )

    try:
        inventory = (
            InventoryService
            .list_inventory_by_warehouse(
                user=user,
                organization=user.organization,
                warehouse=warehouse,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    data = [
        _inventory_to_dict(item)
        for item in inventory
    ]

    return JsonResponse(
        {
            "count": len(data),
            "inventory": data,
        },
        status=200,
    )


def inventory_adjust(
    request,
    inventory_id,
):
    """
    Increase or decrease inventory quantity.
    """

    if request.method != "PUT":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(inventory_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid inventory ID."
            },
            status=400,
        )

    try:
        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": "Invalid JSON."
            },
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "error": "JSON body must be an object."
            },
            status=400,
        )

    if "quantity_change" not in data:
        return JsonResponse(
            {
                "error": "quantity_change is required."
            },
            status=400,
        )

    try:
        inventory = InventoryService.adjust_quantity(
            user=user,
            organization=user.organization,
            inventory_id=inventory_id,
            quantity_change=data[
                "quantity_change"
            ],
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": "Inventory quantity adjusted successfully.",
            "inventory": _inventory_to_dict(
                inventory
            ),
        },
        status=200,
    )


def inventory_reserve(
    request,
    inventory_id,
):
    """
    Reserve inventory quantity.
    """

    if request.method != "PUT":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(inventory_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid inventory ID."
            },
            status=400,
        )

    try:
        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": "Invalid JSON."
            },
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "error": "JSON body must be an object."
            },
            status=400,
        )

    if "quantity" not in data:
        return JsonResponse(
            {
                "error": "quantity is required."
            },
            status=400,
        )

    try:
        inventory = InventoryService.reserve_quantity(
            user=user,
            organization=user.organization,
            inventory_id=inventory_id,
            quantity=data[
                "quantity"
            ],
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": "Inventory reserved successfully.",
            "inventory": _inventory_to_dict(
                inventory
            ),
        },
        status=200,
    )


def inventory_release(
    request,
    inventory_id,
):
    """
    Release reserved inventory quantity.
    """

    if request.method != "PUT":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(inventory_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid inventory ID."
            },
            status=400,
        )

    try:
        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": "Invalid JSON."
            },
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "error": "JSON body must be an object."
            },
            status=400,
        )

    if "quantity" not in data:
        return JsonResponse(
            {
                "error": "quantity is required."
            },
            status=400,
        )

    try:
        inventory = (
            InventoryService
            .release_reserved_quantity(
                user=user,
                organization=user.organization,
                inventory_id=inventory_id,
                quantity=data[
                    "quantity"
                ],
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    return JsonResponse(
        {
            "message": "Reserved inventory released successfully.",
            "inventory": _inventory_to_dict(
                inventory
            ),
        },
        status=200,
    )

def _stock_movement_response(movement):
    """
    Convert a StockMovement document
    into JSON-safe dictionary data.
    """

    return {
        "id": str(movement.id),

        "movement_type": movement.movement_type,
        "quantity": str(movement.quantity),

        "quantity_before": str(
            movement.quantity_before
        ),
        "quantity_after": str(
            movement.quantity_after
        ),

        "reserved_before": str(
            movement.reserved_before
        ),
        "reserved_after": str(
            movement.reserved_after
        ),

        "inventory_id": str(
            movement.inventory.id
        ),

        "product": {
            "id": str(
                movement.product.id
            ),
            "sku": movement.product.sku,
            "name": movement.product.name,
        },

        "warehouse": {
            "id": str(
                movement.warehouse.id
            ),
            "code": movement.warehouse.code,
            "name": movement.warehouse.name,
        },

        "reference_type": (
            movement.reference_type
        ),

        "reference_id": (
            movement.reference_id
        ),

        "notes": movement.notes,

        "created_by": {
            "id": str(
                movement.created_by.id
            ),
            "email": movement.created_by.email,
        },

        "created_at": (
            movement.created_at.isoformat()
        ),
    }


def stock_movement_list(request):
    """
    Return stock movement history for
    the authenticated user's organization.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        movements = (
            StockMovementService.list_movements(
                user=user,
                organization=user.organization,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

    data = [
        _stock_movement_response(movement)
        for movement in movements
    ]

    return JsonResponse(
        {
            "count": len(data),
            "movements": data,
        },
        status=200,
    )

def stock_movement_detail(
    request,
    movement_id,
):
    """
    Return one stock movement.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "error": "Method not allowed."
            },
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error": "Not authenticated."
            },
            status=401,
        )

    try:
        ObjectId(movement_id)

    except (InvalidId, TypeError):
        return JsonResponse(
            {
                "error": "Invalid stock movement ID."
            },
            status=400,
        )

    try:
        movement = StockMovementService.get_movement(
            user=user,
            organization=user.organization,
            movement_id=movement_id,
        )

    except PermissionError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=404,
        )

    return JsonResponse(
        _stock_movement_response(
            movement
        ),
        status=200,
    )


def stock_movements_by_inventory(
    request,
    inventory_id,
):
    """
    Return stock movements for one inventory record.
    """

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(inventory_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid inventory ID."},
            status=400,
        )

    inventory = Inventory.objects(
        id=inventory_id,
        organization=user.organization,
    ).first()

    if not inventory:
        return JsonResponse(
            {"error": "Inventory not found."},
            status=404,
        )

    try:
        movements = (
            StockMovementService.list_inventory_movements(
                user=user,
                organization=user.organization,
                inventory=inventory,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    data = [
        _stock_movement_response(movement)
        for movement in movements
    ]

    return JsonResponse(
        {
            "count": len(data),
            "movements": data,
        },
        status=200,
    )



def stock_movements_by_warehouse(
    request,
    warehouse_id,
):
    """
    Return stock movements for one warehouse.
    """

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(warehouse_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid warehouse ID."},
            status=400,
        )

    warehouse = Warehouse.objects(
        id=warehouse_id,
        organization=user.organization,
    ).first()

    if not warehouse:
        return JsonResponse(
            {"error": "Warehouse not found."},
            status=404,
        )

    try:
        movements = (
            StockMovementService.list_warehouse_movements(
                user=user,
                organization=user.organization,
                warehouse=warehouse,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    data = [
        _stock_movement_response(movement)
        for movement in movements
    ]

    return JsonResponse(
        {
            "count": len(data),
            "movements": data,
        },
        status=200,
    )

def stock_movements_by_type(
    request,
    movement_type,
):
    """
    Return stock movements filtered by movement type.
    """

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    movement_type = movement_type.upper()

    try:
        movements = (
            StockMovementService.list_movements_by_type(
                user=user,
                organization=user.organization,
                movement_type=movement_type,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    data = [
        _stock_movement_response(movement)
        for movement in movements
    ]

    return JsonResponse(
        {
            "count": len(data),
            "movement_type": movement_type,
            "movements": data,
        },
        status=200,
    )

def stock_movements_by_product(
    request,
    product_id,
):
    """
    Return stock movements for one product.
    """

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    try:
        ObjectId(product_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid product ID."},
            status=400,
        )

    product = Product.objects(
        id=product_id,
        organization=user.organization,
    ).first()

    if not product:
        return JsonResponse(
            {"error": "Product not found."},
            status=404,
        )

    try:
        movements = (
            StockMovementService.list_product_movements(
                user=user,
                organization=user.organization,
                product=product,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    data = [
        _stock_movement_response(movement)
        for movement in movements
    ]

    return JsonResponse(
        {
            "count": len(data),
            "movements": data,
        },
        status=200,
    )


def _stock_transfer_response(transfer):
    return {
        "id": str(transfer.id),
        "transfer_number": transfer.transfer_number,
        "status": transfer.status,
        "quantity": str(transfer.quantity),

        "product": {
            "id": str(transfer.product.id),
            "sku": transfer.product.sku,
            "name": transfer.product.name,
        },

        "source_warehouse": {
            "id": str(transfer.source_warehouse.id),
            "code": transfer.source_warehouse.code,
            "name": transfer.source_warehouse.name,
        },

        "destination_warehouse": {
            "id": str(transfer.destination_warehouse.id),
            "code": transfer.destination_warehouse.code,
            "name": transfer.destination_warehouse.name,
        },

        "source_inventory_id": str(
            transfer.source_inventory.id
        ),

        "destination_inventory_id": str(
            transfer.destination_inventory.id
        ),

        "notes": transfer.notes,

        "created_by": {
            "id": str(transfer.created_by.id),
            "email": transfer.created_by.email,
        },

        "created_at": (
            transfer.created_at.isoformat()
            if transfer.created_at
            else None
        ),

        "completed_at": (
            transfer.completed_at.isoformat()
            if transfer.completed_at
            else None
        ),
    }


def stock_transfer_list(request):
    """
    GET:
        List stock transfers.

    POST:
        Execute a warehouse stock transfer.
    """

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if not user.organization:
        return JsonResponse(
            {"error": "User has no organization."},
            status=400,
        )

    # -----------------------------------------
    # GET
    # -----------------------------------------

    if request.method == "GET":

        try:
            StockTransferService._check_permission(
                user,
                "inventory.read",
            )

            transfers = (
                StockTransferRepository
                .list_by_organization(
                    organization=user.organization,
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        data = [
            _stock_transfer_response(transfer)
            for transfer in transfers
        ]

        return JsonResponse(
            {
                "count": len(data),
                "transfers": data,
            },
            status=200,
        )

    # -----------------------------------------
    # POST
    # -----------------------------------------

    if request.method == "POST":

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON."},
                status=400,
            )

        if not isinstance(data, dict):
            return JsonResponse(
                {
                    "error":
                    "JSON body must be an object."
                },
                status=400,
            )

        required_fields = [
            "product_id",
            "source_warehouse_id",
            "destination_warehouse_id",
            "quantity",
        ]

        missing_fields = [
            field
            for field in required_fields
            if data.get(field) is None
        ]

        if missing_fields:
            return JsonResponse(
                {
                    "error": "Missing required fields.",
                    "fields": missing_fields,
                },
                status=400,
            )

        product_id = data.get("product_id")
        source_warehouse_id = data.get(
            "source_warehouse_id"
        )
        destination_warehouse_id = data.get(
            "destination_warehouse_id"
        )

        for value, label in [
            (product_id, "product"),
            (source_warehouse_id, "source warehouse"),
            (
                destination_warehouse_id,
                "destination warehouse",
            ),
        ]:
            try:
                ObjectId(value)
            except (InvalidId, TypeError):
                return JsonResponse(
                    {
                        "error":
                        f"Invalid {label} ID."
                    },
                    status=400,
                )

        product = Product.objects(
            organization=user.organization,
            id=product_id,
        ).first()

        if not product:
            return JsonResponse(
                {"error": "Product not found."},
                status=404,
            )

        source_warehouse = Warehouse.objects(
            organization=user.organization,
            id=source_warehouse_id,
        ).first()

        if not source_warehouse:
            return JsonResponse(
                {
                    "error":
                    "Source warehouse not found."
                },
                status=404,
            )

        destination_warehouse = Warehouse.objects(
            organization=user.organization,
            id=destination_warehouse_id,
        ).first()

        if not destination_warehouse:
            return JsonResponse(
                {
                    "error":
                    "Destination warehouse not found."
                },
                status=404,
            )

        try:
            transfer = (
                StockTransferService.transfer_stock(
                    user=user,
                    organization=user.organization,
                    product=product,
                    source_warehouse=source_warehouse,
                    destination_warehouse=(
                        destination_warehouse
                    ),
                    quantity=data.get("quantity"),
                    notes=data.get("notes", ""),
                )
            )

        except PermissionError as e:
            return JsonResponse(
                {"error": str(e)},
                status=403,
            )

        except ValueError as e:
            return JsonResponse(
                {"error": str(e)},
                status=400,
            )

        return JsonResponse(
            {
                "message":
                "Stock transferred successfully.",
                "transfer":
                _stock_transfer_response(transfer),
            },
            status=201,
        )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )


def stock_transfer_detail(
    request,
    transfer_id,
):
    """
    Return one stock transfer.
    """

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if not user.organization:
        return JsonResponse(
            {"error": "User has no organization."},
            status=400,
        )

    try:
        ObjectId(transfer_id)
    except (InvalidId, TypeError):
        return JsonResponse(
            {"error": "Invalid transfer ID."},
            status=400,
        )

    try:
        StockTransferService._check_permission(
            user,
            "inventory.read",
        )

        transfer = (
            StockTransferRepository.get_by_id(
                organization=user.organization,
                transfer_id=transfer_id,
            )
        )

    except PermissionError as e:
        return JsonResponse(
            {"error": str(e)},
            status=403,
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400,
        )

    if not transfer:
        return JsonResponse(
            {"error": "Stock transfer not found."},
            status=404,
        )

    return JsonResponse(
        _stock_transfer_response(transfer),
        status=200,
    )