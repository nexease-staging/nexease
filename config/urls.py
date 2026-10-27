from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.core import error_handlers

from apps.products.views import (
    product_list,
    product_search,
    product_detail,
    product_create,
    product_deactivate,
    product_activate,
)

from apps.accounts.views import (
    test_login,
    test_current_user,
    test_logout,
    test_protected,
    test_product_create_permission,
    test_tenant_access,
    test_logout_all_devices,
    authentication_audit_logs,
    test_unhandled_exception,
    test_mongodb_exception,
    test_slow_request,
)

from apps.inventory.views import (
    warehouse_detail,
    warehouse_list,
    warehouse_create,
    warehouse_activate,
    warehouse_deactivate,
)


# ==========================================================
# ERROR HANDLERS
# ==========================================================

handler400 = error_handlers.handler400
handler403 = error_handlers.handler403
handler404 = error_handlers.handler404
handler500 = error_handlers.handler500


# ==========================================================
# PRODUCTION-SAFE URLS
# ==========================================================

urlpatterns = [
    # ------------------------------------------------------
    # Django admin
    # ------------------------------------------------------
    path(
        "admin/",
        admin.site.urls,
    ),

    # ------------------------------------------------------
    # Products
    # ------------------------------------------------------
    path(
        "products/",
        product_list,
    ),
    path(
        "products/search/",
        product_search,
    ),
    path(
        "products/<str:product_id>/",
        product_detail,
    ),
    path(
        "products/",
        product_create,
    ),
    path(
        "products/<str:product_id>/deactivate/",
        product_deactivate,
    ),
    path(
        "products/<str:product_id>/activate/",
        product_activate,
    ),

    # ------------------------------------------------------
    # Warehouses
    # ------------------------------------------------------
    path(
        "warehouses/",
        warehouse_list,
    ),
    path(
        "warehouses/create/",
        warehouse_create,
    ),
    path(
        "warehouses/<str:warehouse_id>/",
        warehouse_detail,
    ),
    path(
        "warehouses/<str:warehouse_id>/deactivate/",
        warehouse_deactivate,
    ),
    path(
        "warehouses/<str:warehouse_id>/activate/",
        warehouse_activate,
    ),

    # ------------------------------------------------------
    # Inventory
    # ------------------------------------------------------
    path(
        "inventory/",
        include(
            "apps.inventory.urls"
        ),
    ),

    # ------------------------------------------------------
    # Purchasing
    # ------------------------------------------------------
    path(
        "purchasing/",
        include(
            "apps.purchasing.urls"
        ),
    ),

    # ------------------------------------------------------
    # Sales
    # ------------------------------------------------------
    path(
        "sales/",
        include(
            "apps.sales.urls"
        ),
    ),

    # ------------------------------------------------------
    # Finance
    # ------------------------------------------------------
    path(
        "finance/",
        include(
            "apps.finance.urls"
        ),
    ),

    # ------------------------------------------------------
    # Authentication audit logs
    # ------------------------------------------------------
    path(
        "accounts/authentication-audit-logs/",
        authentication_audit_logs,
        name="authentication_audit_logs",
    ),

    # ------------------------------------------------------
    # Core
    # Includes production health endpoints.
    # Internal core test endpoints are gated inside
    # apps.core.urls.
    # ------------------------------------------------------
    path(
        "",
        include(
            "apps.core.urls"
        ),
    ),

    # ------------------------------------------------------
    # API v1
    # ------------------------------------------------------
    path(
        "api/v1/",
        include(
            "apps.core.api.v1.urls"
        ),
    ),
]


# ==========================================================
# INTERNAL DEVELOPMENT / TEST URLS
#
# These must never be exposed in production.
# settings.py guarantees the flag cannot be enabled in
# production.
# ==========================================================

if settings.ENABLE_INTERNAL_API_TEST_ENDPOINTS:
    urlpatterns += [
        path(
            "test-login/",
            test_login,
            name="test_login",
        ),
        path(
            "test-logout/",
            test_logout,
            name="test_logout",
        ),
        path(
            "test-protected/",
            test_protected,
            name="test_protected",
        ),
        path(
            "test-current-user/",
            test_current_user,
            name="test_current_user",
        ),
        path(
            "test-product-create/",
            test_product_create_permission,
            name="test_product_create_permission",
        ),
        path(
            "test-tenant/",
            test_tenant_access,
            name="test_tenant_access",
        ),
        path(
            "test-logout-all/",
            test_logout_all_devices,
            name="test_logout_all_devices",
        ),
        path(
            "test-unhandled-exception/",
            test_unhandled_exception,
            name="test_unhandled_exception",
        ),
        path(
            "test-mongodb-exception/",
            test_mongodb_exception,
            name="test_mongodb_exception",
        ),
        path(
            "test-slow-request/",
            test_slow_request,
            name="test_slow_request",
        ),
    ]