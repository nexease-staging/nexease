from django.urls import path

from apps.inventory import views

from apps.inventory.views import (
    stock_movement_list,
    stock_movement_detail,
    
)
urlpatterns = [
    path(
        "stock-movements/",
        stock_movement_list,
        name="stock-movement-list",
    ),

    path(
        "stock-movements/inventory/<str:inventory_id>/",
        views.stock_movements_by_inventory,
        name="stock-movements-by-inventory",
    ),

    path(
        "stock-movements/product/<str:product_id>/",
        views.stock_movements_by_product,
        name="stock-movements-by-product",
    ),

    path(
        "stock-movements/warehouse/<str:warehouse_id>/",
        views.stock_movements_by_warehouse,
        name="stock-movements-by-warehouse",
    ),

    path(
        "stock-movements/type/<str:movement_type>/",
        views.stock_movements_by_type,
        name="stock-movements-by-type",
    ),  

    path(
        "stock-movements/<str:movement_id>/",
        stock_movement_detail,
        name="stock-movement-detail",
    ),

    path(
        "transfers/",
        views.stock_transfer_list,
        name="stock-transfer-list",
    ),

    path(
        "transfers/<str:transfer_id>/",
        views.stock_transfer_detail,
        name="stock-transfer-detail",
    ),

    path(
        "product/<str:product_id>/",
        views.inventory_by_product,
        name="inventory-by-product",
    ),

    path(
        "warehouse/<str:warehouse_id>/",
        views.inventory_by_warehouse,
        name="inventory-by-warehouse",
    ),

    path(
        "<str:inventory_id>/adjust/",
        views.inventory_adjust,
        name="inventory-adjust",
    ),

    path(
        "<str:inventory_id>/reserve/",
        views.inventory_reserve,
        name="inventory-reserve",
    ),

    path(
        "<str:inventory_id>/release/",
        views.inventory_release,
        name="inventory-release",
    ),

    path(
        "",
        views.inventory_list,
        name="inventory-list",
    ),

    path(
        "<str:inventory_id>/",
        views.inventory_detail,
        name="inventory-detail",
    ),

]