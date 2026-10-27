from django.urls import (
    path,
)

from apps.inventory.api.v1 import (
    views,
)


app_name = "inventory_api_v1"


urlpatterns = [
    # ==================================================
    # WAREHOUSES
    # ==================================================

    path(
        "warehouses/",
        views.warehouse_collection_api,
        name="warehouse_collection",
    ),

    path(
        (
            "warehouses/"
            "<str:warehouse_id>/activate/"
        ),
        views.warehouse_activate_api,
        name="warehouse_activate",
    ),

    path(
        (
            "warehouses/"
            "<str:warehouse_id>/deactivate/"
        ),
        views.warehouse_deactivate_api,
        name="warehouse_deactivate",
    ),

    path(
        "warehouses/<str:warehouse_id>/",
        views.warehouse_detail_api,
        name="warehouse_detail",
    ),

    # ==================================================
    # INVENTORY
    # ==================================================

    path(
        "inventory/",
        views.inventory_collection_api,
        name="inventory_collection",
    ),
    path(
        (
            "inventory/"
            "<str:inventory_id>/adjust/"
        ),
        views.inventory_adjust_api,
        name="inventory_adjust",
    ),
    path(
        "inventory/<str:inventory_id>/",
        views.inventory_detail_api,
        name="inventory_detail",
    ),
    # ==================================================
    # STOCK MOVEMENT LEDGER
    # ==================================================

    path(
        "stock-movements/",
        views.stock_movement_collection_api,
        name="stock_movement_collection",
    ),

    path(
        (
            "stock-movements/"
            "<str:movement_id>/"
        ),
        views.stock_movement_detail_api,
        name="stock_movement_detail",
    ),
    # ==================================================
    # STOCK TRANSFERS
    # ==================================================

    path(
        "stock-transfers/",
        views.stock_transfer_collection_api,
        name="stock_transfer_collection",
    ),

    path(
        "stock-transfers/<str:transfer_id>/",
        views.stock_transfer_detail_api,
        name="stock_transfer_detail",
    ),
]