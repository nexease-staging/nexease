from django.urls import (
    path,
)

from apps.products.api.v1 import (
    views,
)


app_name = "products_api_v1"


urlpatterns = [
    path(
        "products/",
        views.product_collection_api,
        name="product_collection",
    ),

    path(
        (
            "products/"
            "<str:product_id>/activate/"
        ),
        views.product_activate_api,
        name="product_activate",
    ),

    path(
        (
            "products/"
            "<str:product_id>/deactivate/"
        ),
        views.product_deactivate_api,
        name="product_deactivate",
    ),

    path(
        "products/<str:product_id>/",
        views.product_detail_api,
        name="product_detail",
    ),

    path(
        "categories/",
        views.category_collection_api,
        name="category_collection",
    ),
    path(
        "categories/<str:category_id>/",
        views.category_detail_api,
        name="category_detail",
    ),
    path(
        "categories/<str:category_id>/activate/",
        views.category_activate_api,
        name="category_activate",
    ),
    path(
        "categories/<str:category_id>/deactivate/",
        views.category_deactivate_api,
        name="category_deactivate",
    ),
]