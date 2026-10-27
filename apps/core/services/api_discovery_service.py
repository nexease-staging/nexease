from django.conf import settings

from apps.core.services.api_filtering_service import (
    APIFilteringService,
)
from apps.core.services.api_pagination_service import (
    APIPaginationService,
)
from apps.core.services.api_search_service import (
    APISearchService,
)
from apps.core.services.api_sorting_service import (
    APISortingService,
)
from apps.core.services.build_info_service import (
    BuildInfoService,
)


class APIDiscoveryService:

    API_NAME = "django-ims"
    API_VERSION = "v1"
    API_PREFIX = "/api/v1/"

    @staticmethod
    def get_authentication_endpoints():
        return {
            "csrf": {
                "method":
                    "GET",

                "path":
                    "/api/v1/auth/csrf/",

                "authentication_required":
                    False,

                "status":
                    "available",
            },
            "root": {
                "method":
                    "GET",

                "path":
                    "/api/v1/auth/",

                "authentication_required":
                    False,

                "status":
                    "available",
            },

            "login": {
                "method":
                    "POST",

                "path":
                    "/api/v1/auth/login/",

                "authentication_required":
                    False,

                "status":
                    "available",
            },

            "logout": {
                "method":
                    "POST",

                "path":
                    "/api/v1/auth/logout/",

                "authentication_required":
                    True,

                "status":
                    "available",
            },

            "current_user": {
                "method":
                    "GET",

                "path":
                    "/api/v1/auth/me/",

                "authentication_required":
                    True,

                "status":
                    "available",
            },

            "logout_all": {
                "method":
                    "POST",

                "path":
                    "/api/v1/auth/logout-all/",

                "authentication_required":
                    True,

                "status":
                    "available",
            },
        }

    @staticmethod
    def get_organization_endpoints():
        return {
            "current": {
                "methods": [
                    "GET",
                    "PATCH",
                ],

                "path":
                    "/api/v1/organization/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "update_permission":
                    "organizations.update",

                "status":
                    "available",
            },
        }

    @staticmethod
    def get_authorization_endpoints():
        return {
            "permissions": {
                "method":
                    "GET",

                "path":
                    "/api/v1/permissions/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    False,

                "permission":
                    "permissions.read",

                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],

                "status":
                    "available",
            },

            "roles": {
                "methods": [
                    "GET",
                    "POST",
                ],

                "path":
                    "/api/v1/roles/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permissions": {
                    "GET":
                        "roles.read",

                    "POST":
                        "roles.create",
                },

                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],

                "status":
                    "available",
            },

            "role_detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],

                "path":
                    "/api/v1/roles/{role_id}/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permissions": {
                    "GET":
                        "roles.read",

                    "PATCH":
                        "roles.update",
                },

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },

            "role_permissions": {
                "method":
                    "PATCH",

                "path":
                    (
                        "/api/v1/roles/"
                        "{role_id}/permissions/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "roles.assign_permissions",

                "replacement_semantics":
                    True,

                "system_roles_protected":
                    True,

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },

            "role_activate": {
                "method":
                    "POST",

                "path":
                    (
                        "/api/v1/roles/"
                        "{role_id}/activate/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "roles.activate",

                "idempotent":
                    True,

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },

            "role_deactivate": {
                "method":
                    "POST",

                "path":
                    (
                        "/api/v1/roles/"
                        "{role_id}/deactivate/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "roles.deactivate",

                "idempotent":
                    True,

                "system_roles_protected":
                    True,

                "assigned_user_protection":
                    True,

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },
        }
    
    @staticmethod
    def get_capabilities():
        return {
            "authentication": {
                "type":
                    "session",

                "cookie_name":
                    settings
                    .SESSION_COOKIE_NAME,

                "csrf_required_for_unsafe_methods":
                    True,

                "csrf_endpoint":
                    "/api/v1/auth/csrf/",

                "csrf_cookie_name":
                    settings
                    .CSRF_COOKIE_NAME,

                "csrf_header_name":
                    "X-CSRFToken",

                "unsafe_methods": [
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                ],
            },

            "tenant_isolation": {
                "enabled":
                    True,

                "source":
                    "authenticated_session",

                "client_organization_id_trusted":
                    False,
            },

            "authorization": {
                "enabled":
                    True,

                "model":
                    "role_permissions",

                "default_policy":
                    "deny",
            },

            "pagination": {
                "enabled":
                    True,

                "page_parameter":
                    "page",

                "page_size_parameter":
                    "page_size",

                "default_page":
                    (
                        APIPaginationService
                        .DEFAULT_PAGE
                    ),

                "default_page_size":
                    (
                        APIPaginationService
                        .DEFAULT_PAGE_SIZE
                    ),

                "maximum_page_size":
                    (
                        APIPaginationService
                        .MAX_PAGE_SIZE
                    ),
            },

            "filtering": {
                "enabled":
                    True,

                "policy":
                    "endpoint_whitelist",

                "supported_lookups":
                    sorted(
                        APIFilteringService
                        .ALLOWED_LOOKUPS
                    ),
            },

            "search": {
                "enabled":
                    True,

                "parameter":
                    (
                        APISearchService
                        .DEFAULT_PARAMETER
                    ),

                "minimum_length":
                    (
                        APISearchService
                        .MIN_LENGTH
                    ),

                "maximum_length":
                    (
                        APISearchService
                        .MAX_LENGTH
                    ),

                "regex_input_escaped":
                    True,
            },

            "sorting": {
                "enabled":
                    True,

                "parameter":
                    "sort",

                "descending_prefix":
                    "-",

                "multiple_fields":
                    True,

                "maximum_fields":
                    (
                        APISortingService
                        .MAX_SORT_FIELDS
                    ),

                "stable_tiebreaker":
                    True,
            },

            "rate_limiting": {
                "enabled":
                    True,

                "response_status":
                    429,

                "headers": {
                    "limit":
                        "X-RateLimit-Limit",

                    "remaining":
                        "X-RateLimit-Remaining",

                    "reset":
                        "X-RateLimit-Reset",

                    "retry_after":
                        "Retry-After",
                },
            },

            "correlation": {
                "server_request_header":
                    "X-Request-ID",

                "client_request_header":
                    "X-Correlation-ID",

                "client_correlation_optional":
                    True,

                "client_request_id_trusted":
                    False,
            },

            "response_contract": {
                "success_field":
                    "success",

                "data_field":
                    "data",

                "error_field":
                    "error",

                "request_id_field":
                    "request_id",

                "metadata_field":
                    "meta",
            },
        }

    @staticmethod
    def get_category_endpoints():
        return {
            "list": {
                "method":
                    "GET",

                "path":
                    "/api/v1/categories/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "products.read",

                "active_only":
                    True,

                "status":
                    "available",
            },
        }

    @staticmethod
    def get_product_endpoints():
        return {
            # ==============================================
            # COLLECTION
            # ==============================================

            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],

                "path":
                    "/api/v1/products/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permissions": {
                    "GET":
                        "products.read",

                    "POST":
                        "products.create",
                },

                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],

                "filters": {
                    "is_active":
                        "boolean",
                },

                "search_fields": [
                    "sku",
                    "name",
                    "brand",
                    "barcode",
                ],

                "sort_fields": [
                    "sku",
                    "name",
                    "brand",
                    "unit",
                    "cost_price",
                    "selling_price",
                    "created_at",
                    "updated_at",
                ],

                "default_sort": [
                    "-created_at",
                    "id",
                ],

                "default_page_size":
                    25,

                "maximum_page_size":
                    100,

                "create_fields": [
                    "sku",
                    "name",
                    "description",
                    "category_id",
                    "brand",
                    "unit",
                    "cost_price",
                    "selling_price",
                    "barcode",
                ],

                "required_create_fields": [
                    "sku",
                    "name",
                    "category_id",
                    "unit",
                ],

                "status":
                    "available",
            },

            # ==============================================
            # DETAIL
            # ==============================================

            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],

                "path":
                    (
                        "/api/v1/products/"
                        "{product_id}/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permissions": {
                    "GET":
                        "products.read",

                    "PATCH":
                        "products.update",
                },

                "editable_fields": [
                    "sku",
                    "name",
                    "description",
                    "category_id",
                    "brand",
                    "unit",
                    "cost_price",
                    "selling_price",
                    "barcode",
                ],

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },

            # ==============================================
            # ACTIVATE
            # ==============================================

            "activate": {
                "method":
                    "POST",

                "path":
                    (
                        "/api/v1/products/"
                        "{product_id}/activate/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "products.update",

                "idempotent":
                    True,

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },

            # ==============================================
            # DEACTIVATE
            # ==============================================

            "deactivate": {
                "method":
                    "POST",

                "path":
                    (
                        "/api/v1/products/"
                        "{product_id}/deactivate/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "products.delete",

                "idempotent":
                    True,

                "hard_delete":
                    False,

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },
        }

    @staticmethod
    def get_customer_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/customers/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "customers.read",
                    "POST":
                        "customers.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "status":
                    "available",
            },

            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],
                "path": (
                    "/api/v1/customers/"
                    "{customer_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "customers.read",
                    "PATCH":
                        "customers.update",
                },
                "editable_fields": [
                    "name",
                    "email",
                    "phone",
                    "gstin",
                    "billing_address",
                    "shipping_address",
                    "city",
                    "state",
                    "country",
                    "pincode",
                ],
                "status":
                    "available",
            },

            "activate": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/customers/"
                    "{customer_id}/activate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "customers.update",
                "status":
                    "available",
            },

            "deactivate": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/customers/"
                    "{customer_id}/deactivate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "customers.update",
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_sales_order_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/sales-orders/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "sales_orders.read",
                    "POST":
                        "sales_orders.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "customer_id":
                        "object_id",
                    "warehouse_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "customer_id",
                    "warehouse_id",
                    "order_date",
                    "expected_delivery_date",
                    "items",
                    "notes",
                ],
                "server_calculated_fields": [
                    "so_number",
                    "subtotal",
                    "tax_amount",
                    "discount_amount",
                    "total_amount",
                    "status",
                ],
                "status":
                    "available",
            },

            "detail": {
                "methods": [
                    "GET",
                    "PUT",
                ],
                "path": (
                    "/api/v1/sales-orders/"
                    "{sales_order_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "sales_orders.read",
                    "PUT":
                        "sales_orders.update",
                },
                "editable_statuses": [
                    "DRAFT",
                ],
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },

            "confirm": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/sales-orders/"
                    "{sales_order_id}/confirm/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "sales_orders.update",
                "from_statuses": [
                    "DRAFT",
                ],
                "inventory_effect":
                    "reserve",
                "status":
                    "available",
            },

            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/sales-orders/"
                    "{sales_order_id}/cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "sales_orders.cancel",
                "inventory_effect":
                    "release_reservation",
                "status":
                    "available",
            },

            "fulfill": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/sales-orders/"
                    "{sales_order_id}/fulfill/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "sales_orders.fulfill",
                "from_statuses": [
                    "CONFIRMED",
                    "PARTIALLY_FULFILLED",
                ],
                "inventory_effect":
                    "stock_out",
                "supports_partial_fulfillment":
                    True,
                "status":
                    "available",
            },
        }
    @staticmethod
    def get_invoice_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/invoices/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "invoices.read",
                    "POST":
                        "invoices.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "customer_id":
                        "object_id",
                    "sales_order_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "sales_order_id",
                    "invoice_date",
                    "due_date",
                    "notes",
                ],
                "creation_rule": (
                    "One invoice per fulfilled "
                    "Sales Order."
                ),
                "status":
                    "available",
            },

            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/invoices/"
                    "{invoice_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "invoices.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },

            "issue": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/invoices/"
                    "{invoice_id}/issue/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "invoices.issue",
                "from_statuses": [
                    "DRAFT",
                ],
                "accounting_effect":
                    "post_sales_journal",
                "status":
                    "available",
            },

            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/invoices/"
                    "{invoice_id}/cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "invoices.cancel",
                "blocked_statuses": [
                    "PARTIALLY_PAID",
                    "PAID",
                    "CANCELLED",
                ],
                "status":
                    "available",
            },

            "record_payment": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/invoices/"
                    "{invoice_id}/"
                    "record-payment/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "invoices.record_payment",
                "eligible_statuses": [
                    "ISSUED",
                    "PARTIALLY_PAID",
                ],
                "accounting_effect":
                    "post_customer_payment",
                "bank_effect":
                    "money_in",
                "status":
                    "available",
            },

            "payment_accounts": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "invoice-bank-accounts/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "invoices.record_payment",
                "sensitive_account_numbers":
                    "masked",
                "status":
                    "available",
            },
        }
    @staticmethod
    def get_customer_payment_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "customer-payments/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "customer_payments.read",
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "customer_id":
                        "object_id",
                    "invoice_id":
                        "object_id",
                    "bank_account_id":
                        "object_id",
                    "payment_method":
                        "string",
                },
                "immutable":
                    True,
                "status":
                    "available",
            },

            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "customer-payments/"
                    "{payment_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "customer_payments.read",
                "cross_tenant_behavior":
                    "not_found",
                "sensitive_account_numbers":
                    "masked",
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_accounts_receivable_endpoints():
        return {
            "summary": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "accounts-receivable/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "invoices.read",
                "includes": [
                    "current_receivables",
                    "overdue_receivables",
                    "customer_totals",
                ],
                "status":
                    "available",
            },

            "aging": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "accounts-receivable/"
                    "aging/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "invoices.read",
                "buckets": [
                    "current",
                    "days_1_30",
                    "days_31_60",
                    "days_61_90",
                    "days_over_90",
                ],
                "credit_notes_reduce_receivable":
                    True,
                "status":
                    "available",
            },
        }
    @staticmethod
    def get_supplier_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/suppliers/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "suppliers.read",
                    "POST":
                        "suppliers.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "status":
                    "available",
            },

            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],
                "path": (
                    "/api/v1/suppliers/"
                    "{supplier_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "suppliers.read",
                    "PATCH":
                        "suppliers.update",
                },
                "editable_fields": [
                    "name",
                    "email",
                    "phone",
                    "gstin",
                    "address",
                    "city",
                    "state",
                    "country",
                    "pincode",
                ],
                "status":
                    "available",
            },

            "activate": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/suppliers/"
                    "{supplier_id}/activate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "suppliers.update",
                "status":
                    "available",
            },

            "deactivate": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/suppliers/"
                    "{supplier_id}/deactivate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "suppliers.update",
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_purchase_order_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "purchase-orders/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "purchase_orders.read",
                    "POST":
                        "purchase_orders.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "supplier_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "supplier_id",
                    "order_date",
                    "expected_delivery_date",
                    "items",
                    "notes",
                ],
                "status":
                    "available",
            },

            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],
                "path": (
                    "/api/v1/"
                    "purchase-orders/"
                    "{purchase_order_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "purchase_orders.read",
                    "PATCH":
                        "purchase_orders.update",
                },
                "editable_statuses": [
                    "DRAFT",
                ],
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },

            "confirm": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "purchase-orders/"
                    "{purchase_order_id}/"
                    "confirm/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "purchase_orders.update",
                "from_statuses": [
                    "DRAFT",
                ],
                "status":
                    "available",
            },

            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "purchase-orders/"
                    "{purchase_order_id}/"
                    "cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "purchase_orders.cancel",
                "blocked_statuses": [
                    "PARTIALLY_RECEIVED",
                    "RECEIVED",
                    "CANCELLED",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_goods_receipt_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "goods-receipts/"
                ),
                "authentication_required": True,
                "tenant_scoped": True,
                "permissions": {
                    "GET":
                        "goods_receipts.read",
                    "POST":
                        "goods_receipts.create",
                },
                "query_capabilities": [
                    "search",
                    "sorting",
                    "pagination",
                ],
                "create_fields": [
                    "purchase_order_id",
                    "warehouse_id",
                    "items",
                    "notes",
                ],
                "status": "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "goods-receipts/"
                    "{goods_receipt_id}/"
                ),
                "authentication_required": True,
                "tenant_scoped": True,
                "permission":
                    "goods_receipts.read",
                "cross_tenant_behavior":
                    "not_found",
                "status": "available",
            },
        }

    @staticmethod
    def get_vendor_bill_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/vendor-bills/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "bills.read",
                    "POST":
                        "bills.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "supplier_id":
                        "object_id",
                    "purchase_order_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "purchase_order_id",
                    (
                        "supplier_invoice_"
                        "number"
                    ),
                    "bill_date",
                    "due_date",
                    "notes",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/vendor-bills/"
                    "{bill_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bills.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "post": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/vendor-bills/"
                    "{bill_id}/post/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bills.post",
                "from_statuses": [
                    "DRAFT",
                ],
                "status":
                    "available",
            },
            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/vendor-bills/"
                    "{bill_id}/cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bills.cancel",
                "blocked_statuses": [
                    "PARTIALLY_PAID",
                    "PAID",
                    "CANCELLED",
                ],
                "status":
                    "available",
            },
            "record_payment": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/vendor-bills/"
                    "{bill_id}/payments/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bills.record_payment",
                "allowed_statuses": [
                    "POSTED",
                    "PARTIALLY_PAID",
                ],
                "status":
                    "available",
            },
            "bank_accounts": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/vendor-bills/"
                    "bank-accounts/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bills.record_payment",
                "status":
                    "available",
            },
            "accounts_payable": {
                "methods": [
                    "GET",
                ],
                "path":
                    "/api/v1/accounts-payable/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bills.read",
                "status":
                    "available",
            },
        }
    @staticmethod
    def get_purchase_return_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/purchase-returns/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "purchase_returns.read",
                    "POST":
                        "purchase_returns.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "supplier_id":
                        "object_id",
                    "purchase_order_id":
                        "object_id",
                    "vendor_bill_id":
                        "object_id",
                    "warehouse_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "purchase_order_id",
                    "vendor_bill_id",
                    "warehouse_id",
                    "return_date",
                    "items",
                    "reason",
                    "notes",
                ],
                "required_create_fields": [
                    "purchase_order_id",
                    "vendor_bill_id",
                    "warehouse_id",
                    "items",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/purchase-returns/"
                    "{purchase_return_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "purchase_returns.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "confirm": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/purchase-returns/"
                    "{purchase_return_id}/"
                    "confirm/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "purchase_returns.confirm",
                "from_statuses": [
                    "DRAFT",
                ],
                "effects": [
                    "inventory_reduction",
                    "stock_movements",
                ],
                "status":
                    "available",
            },
            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/purchase-returns/"
                    "{purchase_return_id}/"
                    "cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "purchase_returns.cancel",
                "from_statuses": [
                    "DRAFT",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_vendor_debit_note_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "vendor-debit-notes/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "vendor_debit_notes.read",
                    "POST":
                        "vendor_debit_notes.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "supplier_id":
                        "object_id",
                    "purchase_order_id":
                        "object_id",
                    "purchase_return_id":
                        "object_id",
                    "vendor_bill_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "purchase_return_id",
                    "debit_note_date",
                    "reason",
                    "notes",
                ],
                "required_create_fields": [
                    "purchase_return_id",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "vendor-debit-notes/"
                    "{debit_note_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "vendor_debit_notes.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "issue": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "vendor-debit-notes/"
                    "{debit_note_id}/issue/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "vendor_debit_notes.issue",
                "from_statuses": [
                    "DRAFT",
                ],
                "effects": [
                    "payable_reduction",
                    "accounting_journal",
                ],
                "status":
                    "available",
            },
            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "vendor-debit-notes/"
                    "{debit_note_id}/cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "vendor_debit_notes.cancel",
                "from_statuses": [
                    "DRAFT",
                ],
                "status":
                    "available",
            },
        }
    @staticmethod
    def get_sales_return_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/sales-returns/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "sales_returns.read",
                    "POST":
                        "sales_returns.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "customer_id":
                        "object_id",
                    "sales_order_id":
                        "object_id",
                    "invoice_id":
                        "object_id",
                    "warehouse_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "invoice_id",
                    "return_date",
                    "items",
                    "reason",
                    "notes",
                ],
                "required_create_fields": [
                    "invoice_id",
                    "items",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/sales-returns/"
                    "{sales_return_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "sales_returns.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "confirm": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/sales-returns/"
                    "{sales_return_id}/"
                    "confirm/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "sales_returns.confirm",
                "from_statuses": [
                    "DRAFT",
                ],
                "effects": [
                    "inventory_restoration",
                    "stock_movements",
                ],
                "status":
                    "available",
            },
            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/sales-returns/"
                    "{sales_return_id}/"
                    "cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "sales_returns.cancel",
                "from_statuses": [
                    "DRAFT",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_credit_note_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/credit-notes/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "credit_notes.read",
                    "POST":
                        "credit_notes.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "customer_id":
                        "object_id",
                    "invoice_id":
                        "object_id",
                    "sales_return_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "sales_return_id",
                    "credit_note_date",
                    "reason",
                    "notes",
                ],
                "required_create_fields": [
                    "sales_return_id",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/credit-notes/"
                    "{credit_note_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "credit_notes.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "issue": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/credit-notes/"
                    "{credit_note_id}/issue/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "credit_notes.issue",
                "from_statuses": [
                    "DRAFT",
                ],
                "effects": [
                    "receivable_reduction",
                    "accounting_journal",
                ],
                "status":
                    "available",
            },
            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/credit-notes/"
                    "{credit_note_id}/cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "credit_notes.cancel",
                "from_statuses": [
                    "DRAFT",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_chart_of_account_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "chart-of-accounts/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "chart_of_accounts.read",
                    "POST":
                        "chart_of_accounts.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "account_type":
                        "string",
                    "account_subtype":
                        "string",
                    "normal_balance":
                        "string",
                    "is_system_account":
                        "boolean",
                    "is_active":
                        "boolean",
                    "allow_manual_posting":
                        "boolean",
                },
                "create_fields": [
                    "account_code",
                    "account_name",
                    "account_type",
                    "account_subtype",
                    "description",
                    "allow_manual_posting",
                ],
                "required_create_fields": [
                    "account_code",
                    "account_name",
                    "account_type",
                ],
                "protected_fields": [
                    "organization_id",
                    "normal_balance",
                    "system_key",
                    "is_system_account",
                    "is_active",
                    "created_by",
                    "created_at",
                    "updated_at",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],
                "path": (
                    "/api/v1/"
                    "chart-of-accounts/"
                    "{account_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "chart_of_accounts.read",
                    "PATCH":
                        "chart_of_accounts.update",
                },
                "editable_fields": [
                    "account_name",
                    "account_subtype",
                    "description",
                    "allow_manual_posting",
                ],
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "deactivate": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "chart-of-accounts/"
                    "{account_id}/deactivate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission": (
                    "chart_of_accounts."
                    "deactivate"
                ),
                "system_accounts_protected":
                    True,
                "hard_delete":
                    False,
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_journal_entry_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "journal-entries/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "journal_entries.read",
                    "POST":
                        "journal_entries.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "status":
                        "string",
                    "source_type":
                        "string",
                    "source_id":
                        "string",
                },
                "create_fields": [
                    "journal_date",
                    "description",
                    "lines",
                ],
                "required_create_fields": [
                    "journal_date",
                    "lines",
                ],
                "line_fields": [
                    "account_id",
                    "description",
                    "debit",
                    "credit",
                ],
                "forced_source_type":
                    "MANUAL",
                "protected_fields": [
                    "organization_id",
                    "journal_number",
                    "source_type",
                    "source_id",
                    "status",
                    "total_debit",
                    "total_credit",
                    "posted_at",
                    "reversed_at",
                    "reversed_by",
                    "reversal_of",
                    "created_by",
                    "created_at",
                    "updated_at",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],
                "path": (
                    "/api/v1/"
                    "journal-entries/"
                    "{journal_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "journal_entries.read",
                    "PATCH":
                        "journal_entries.create",
                },
                "editable_statuses": [
                    "DRAFT",
                ],
                "editable_fields": [
                    "journal_date",
                    "description",
                    "lines",
                ],
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "post": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "journal-entries/"
                    "{journal_id}/post/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "journal_entries.post",
                "from_statuses": [
                    "DRAFT",
                ],
                "effects": [
                    "journal_validation",
                    "ledger_posting",
                ],
                "status":
                    "available",
            },
            "reverse": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "journal-entries/"
                    "{journal_id}/reverse/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "journal_entries.reverse",
                "from_statuses": [
                    "POSTED",
                ],
                "fields": [
                    "reversal_date",
                    "description",
                ],
                "effects": [
                    "reversal_journal_creation",
                    "reversal_journal_posting",
                    "original_journal_reversal",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_general_ledger_endpoints():
        return {
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "general-ledger/"
                    "{account_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "general_ledger.read",
                "query_parameters": {
                    "start_date":
                        "ISO-8601 date or datetime",
                    "end_date":
                        "ISO-8601 date or datetime",
                },
                "posted_journals_only":
                    True,
                "includes": [
                    "opening_balance",
                    "movements",
                    "running_balance",
                    "closing_balance",
                ],
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_trial_balance_endpoints():
        return {
            "summary": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "trial-balance/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "trial_balance.read",
                "query_parameters": {
                    "as_of_date":
                        "ISO-8601 date or datetime",
                    "include_zero_balances":
                        "boolean",
                },
                "posted_journals_only":
                    True,
                "includes": [
                    "account_balances",
                    "total_debit_balance",
                    "total_credit_balance",
                    "difference",
                    "is_balanced",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_bank_account_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/bank-accounts/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "bank_accounts.read",
                    "POST":
                        "bank_accounts.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "account_type":
                        "string",
                    "currency":
                        "string",
                    "is_active":
                        "boolean",
                },
                "create_fields": [
                    "account_name",
                    "account_type",
                    "bank_name",
                    "account_number",
                    "ifsc_code",
                    "currency",
                    "opening_balance",
                ],
                "required_create_fields": [
                    "account_name",
                    "account_type",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],
                "path": (
                    "/api/v1/bank-accounts/"
                    "{bank_account_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "bank_accounts.read",
                    "PATCH":
                        "bank_accounts.update",
                },
                "editable_fields": [
                    "account_name",
                    "bank_name",
                    "account_number",
                    "ifsc_code",
                ],
                "protected_fields": [
                    "account_type",
                    "currency",
                    "opening_balance",
                    "current_balance",
                    "is_active",
                ],
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "deactivate": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-accounts/"
                    "{bank_account_id}/deactivate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_accounts.deactivate",
                "hard_delete":
                    False,
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_bank_transaction_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-transactions/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "bank_transactions.read",
                    "POST":
                        "bank_transactions.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "bank_account_id":
                        "object_id",
                    "transaction_type":
                        "string",
                    "reconciliation_status":
                        "string",
                },
                "create_fields": [
                    "bank_account_id",
                    "transaction_type",
                    "transaction_date",
                    "amount",
                    "reference_type",
                    "reference_id",
                    "external_reference",
                    "description",
                ],
                "required_create_fields": [
                    "bank_account_id",
                    "transaction_type",
                    "transaction_date",
                    "amount",
                ],
                "manual_transaction_types": [
                    "MONEY_IN",
                    "MONEY_OUT",
                    "BANK_CHARGE",
                    "INTEREST",
                    "OTHER_IN",
                    "OTHER_OUT",
                ],
                "system_transaction_types": [
                    "OPENING_BALANCE",
                    "TRANSFER_IN",
                    "TRANSFER_OUT",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/bank-transactions/"
                    "{transaction_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_transactions.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "reconcile": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-transactions/"
                    "{transaction_id}/reconcile/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_transactions.reconcile",
                "from_statuses": [
                    "UNRECONCILED",
                ],
                "to_status":
                    "RECONCILED",
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_bank_transfer_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/bank-transfers/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "bank_transfers.read",
                    "POST":
                        "bank_transfers.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "source_account_id":
                        "object_id",
                    "destination_account_id":
                        "object_id",
                    "status":
                        "string",
                },
                "create_fields": [
                    "source_account_id",
                    "destination_account_id",
                    "transfer_date",
                    "amount",
                    "reference",
                    "notes",
                ],
                "required_create_fields": [
                    "source_account_id",
                    "destination_account_id",
                    "transfer_date",
                    "amount",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/bank-transfers/"
                    "{transfer_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_transfers.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "post": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-transfers/"
                    "{transfer_id}/post/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_transfers.post",
                "from_statuses": [
                    "DRAFT",
                ],
                "effects": [
                    "source_balance_reduction",
                    "destination_balance_increase",
                    "transfer_out_transaction",
                    "transfer_in_transaction",
                ],
                "status":
                    "available",
            },
            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-transfers/"
                    "{transfer_id}/cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_transfers.cancel",
                "from_statuses": [
                    "DRAFT",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_bank_statement_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/bank-statements/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "bank_statements.read",
                    "POST":
                        "bank_statements.create",
                },
                "content_type": {
                    "POST":
                        "multipart/form-data",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "bank_account_id":
                        "object_id",
                    "status":
                        "string",
                    "source_type":
                        "string",
                },
                "import_fields": [
                    "file",
                    "bank_account_id",
                    "statement_start_date",
                    "statement_end_date",
                    "opening_balance",
                    "closing_balance",
                ],
                "required_import_fields": [
                    "file",
                    "bank_account_id",
                    "statement_start_date",
                    "statement_end_date",
                    "opening_balance",
                    "closing_balance",
                ],
                "supported_file_types": [
                    "CSV",
                    "XLSX",
                ],
                "maximum_file_size_bytes":
                    5242880,
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/bank-statements/"
                    "{statement_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "cancel": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-statements/"
                    "{statement_id}/cancel/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.cancel",
                "from_statuses": [
                    "IMPORTED",
                    "PARTIALLY_RECONCILED",
                ],
                "status":
                    "available",
            },
            "auto_match_line": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-statements/"
                    "{statement_id}/lines/"
                    "{line_number}/auto-match/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.reconcile",
                "from_line_statuses": [
                    "UNMATCHED",
                ],
                "effects": [
                    "match_candidate_search",
                    "transaction_reconciliation",
                    "statement_status_update",
                ],
                "status":
                    "available",
            },
            "match_line": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-statements/"
                    "{statement_id}/lines/"
                    "{line_number}/match/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.reconcile",
                "fields": [
                    "transaction_id",
                ],
                "required_fields": [
                    "transaction_id",
                ],
                "from_line_statuses": [
                    "UNMATCHED",
                ],
                "effects": [
                    "transaction_reconciliation",
                    "statement_status_update",
                ],
                "status":
                    "available",
            },
            "ignore_line": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-statements/"
                    "{statement_id}/lines/"
                    "{line_number}/ignore/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.reconcile",
                "from_line_statuses": [
                    "UNMATCHED",
                ],
                "effects": [
                    "line_ignored",
                    "statement_status_update",
                ],
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_bank_payment_suggestion_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.read",
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "statement_id":
                        "object_id",
                    "invoice_id":
                        "object_id",
                    "vendor_bill_id":
                        "object_id",
                    "suggestion_type":
                        "string",
                    "status":
                        "string",
                },
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                ],
                "path": (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "{suggestion_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "generate": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/bank-statements/"
                    "{statement_id}/lines/"
                    "{line_number}/"
                    "payment-suggestion/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.reconcile",
                "from_line_statuses": [
                    "UNMATCHED",
                ],
                "suggestion_types": [
                    "CUSTOMER_RECEIPT",
                    "SUPPLIER_PAYMENT",
                ],
                "status":
                    "available",
            },
            "confirm": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "{suggestion_id}/confirm/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.reconcile",
                "from_statuses": [
                    "PENDING",
                ],
                "to_status":
                    "CONFIRMED",
                "status":
                    "available",
            },
            "reject": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "{suggestion_id}/reject/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.reconcile",
                "from_statuses": [
                    "PENDING",
                ],
                "to_status":
                    "REJECTED",
                "status":
                    "available",
            },
            "execute": {
                "methods": [
                    "POST",
                ],
                "path": (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "{suggestion_id}/execute/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "bank_statements.reconcile",
                "from_statuses": [
                    "CONFIRMED",
                ],
                "requires_unmatched_line":
                    True,
                "effects": [
                    "customer_or_supplier_payment",
                    "bank_transaction",
                    "statement_line_match",
                    "transaction_reconciliation",
                    "statement_status_update",
                ],
                "compensation_on_failure":
                    True,
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_warehouse_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/warehouses/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "warehouses.read",
                    "POST":
                        "warehouses.create",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "is_active":
                        "boolean",
                    "country":
                        "string",
                    "state":
                        "string",
                    "city":
                        "string",
                },
                "create_fields": [
                    "name",
                    "code",
                    "address",
                    "city",
                    "state",
                    "country",
                    "pincode",
                ],
                "required_create_fields": [
                    "name",
                    "code",
                ],
                "status":
                    "available",
            },
            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],
                "path": (
                    "/api/v1/warehouses/"
                    "{warehouse_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "warehouses.read",
                    "PATCH":
                        "warehouses.update",
                },
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "activate": {
                "method":
                    "POST",
                "path": (
                    "/api/v1/warehouses/"
                    "{warehouse_id}/activate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "warehouses.update",
                "idempotent":
                    True,
                "status":
                    "available",
            },
            "deactivate": {
                "method":
                    "POST",
                "path": (
                    "/api/v1/warehouses/"
                    "{warehouse_id}/deactivate/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "warehouses.update",
                "idempotent":
                    True,
                "hard_delete":
                    False,
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_inventory_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/inventory/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "inventory.read",
                    "POST":
                        "inventory.create",
                },
                "query_capabilities": [
                    "filtering",
                    "sorting",
                    "pagination",
                ],
                "filters": {
                    "product_id":
                        "object_id",
                    "warehouse_id":
                        "object_id",
                },
                "create_fields": [
                    "product_id",
                    "warehouse_id",
                    "quantity",
                ],
                "required_create_fields": [
                    "product_id",
                    "warehouse_id",
                ],
                "status":
                    "available",
            },
            "detail": {
                "method":
                    "GET",
                "path": (
                    "/api/v1/inventory/"
                    "{inventory_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "inventory.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
            "adjust": {
                "method":
                    "POST",
                "path": (
                    "/api/v1/inventory/"
                    "{inventory_id}/adjust/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "inventory.adjust",
                "fields": [
                    "quantity_change",
                    "reference_type",
                    "reference_id",
                    "notes",
                ],
                "creates_ledger_entry":
                    True,
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_stock_movement_endpoints():
        return {
            "collection": {
                "method":
                    "GET",
                "path":
                    "/api/v1/stock-movements/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "inventory.read",
                "immutable":
                    True,
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": [
                    "inventory_id",
                    "product_id",
                    "warehouse_id",
                    "movement_type",
                    "reference_type",
                    "reference_id",
                ],
                "status":
                    "available",
            },
            "detail": {
                "method":
                    "GET",
                "path": (
                    "/api/v1/stock-movements/"
                    "{movement_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "inventory.read",
                "immutable":
                    True,
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
        }

    @staticmethod
    def get_stock_transfer_endpoints():
        return {
            "collection": {
                "methods": [
                    "GET",
                    "POST",
                ],
                "path":
                    "/api/v1/stock-transfers/",
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permissions": {
                    "GET":
                        "inventory.read",
                    "POST":
                        "inventory.transfer",
                },
                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],
                "filters": [
                    "product_id",
                    "source_warehouse_id",
                    "destination_warehouse_id",
                    "status",
                ],
                "create_fields": [
                    "product_id",
                    "source_warehouse_id",
                    "destination_warehouse_id",
                    "quantity",
                    "notes",
                ],
                "status":
                    "available",
            },
            "detail": {
                "method":
                    "GET",
                "path": (
                    "/api/v1/stock-transfers/"
                    "{transfer_id}/"
                ),
                "authentication_required":
                    True,
                "tenant_scoped":
                    True,
                "permission":
                    "inventory.read",
                "cross_tenant_behavior":
                    "not_found",
                "status":
                    "available",
            },
        }
    @staticmethod
    def get_manifest():
        build_info = (
            BuildInfoService
            .get_info()
        )

        return {
            "api": {
                "name":
                    (
                        APIDiscoveryService
                        .API_NAME
                    ),

                "version":
                    (
                        APIDiscoveryService
                        .API_VERSION
                    ),

                "prefix":
                    (
                        APIDiscoveryService
                        .API_PREFIX
                    ),

                "status":
                    "available",

                "application_version":
                    build_info.get(
                        "version"
                    ),
            },

            "endpoints": {
                "authentication":
                    (
                        APIDiscoveryService
                        .get_authentication_endpoints()
                    ),

                "organization":
                    (
                        APIDiscoveryService
                        .get_organization_endpoints()
                    ),
                    
                "authorization":
                    (
                        APIDiscoveryService
                        .get_authorization_endpoints()
                    ),

                "users":
                    (
                        APIDiscoveryService
                        .get_user_endpoints()
                    ),
                "categories":
                    (
                        APIDiscoveryService
                        .get_category_endpoints()
                    ),

                "products":
                    (
                        APIDiscoveryService
                        .get_product_endpoints()
                    ),
                "customers":
                    (
                        APIDiscoveryService
                        .get_customer_endpoints()
                    ),
                "sales_orders":
                    (
                        APIDiscoveryService
                        .get_sales_order_endpoints()
                    ),
                "invoices":
                    (
                        APIDiscoveryService
                        .get_invoice_endpoints()
                    ),
                "sales_returns": (
                    APIDiscoveryService
                    .get_sales_return_endpoints()
                ),

                "credit_notes": (
                    APIDiscoveryService
                    .get_credit_note_endpoints()
                ),
                "customer_payments":
                    (
                        APIDiscoveryService
                        .get_customer_payment_endpoints()
                    ),

                "accounts_receivable":
                    (
                        APIDiscoveryService
                        .get_accounts_receivable_endpoints()
                    ),
                "suppliers":
                    (
                        APIDiscoveryService
                        .get_supplier_endpoints()
                    ),
                "purchase_orders":
                    (
                        APIDiscoveryService
                        .get_purchase_order_endpoints()
                    ),
                "goods_receipts": (
                    APIDiscoveryService
                    .get_goods_receipt_endpoints()
                ),
                "vendor_bills": (
                    APIDiscoveryService
                    .get_vendor_bill_endpoints()
                ),
                "purchase_returns": (
                    APIDiscoveryService
                    .get_purchase_return_endpoints()
                ),

                "vendor_debit_notes": (
                    APIDiscoveryService
                    .get_vendor_debit_note_endpoints()
                ),

                "chart_of_accounts": (
                    APIDiscoveryService
                    .get_chart_of_account_endpoints()
                ),

                "journal_entries": (
                    APIDiscoveryService
                    .get_journal_entry_endpoints()
                ),

                "general_ledger": (
                    APIDiscoveryService
                    .get_general_ledger_endpoints()
                ),

                "trial_balance": (
                    APIDiscoveryService
                    .get_trial_balance_endpoints()
                ),

                "bank_accounts": (
                    APIDiscoveryService
                    .get_bank_account_endpoints()
                ),

                "bank_transactions": (
                    APIDiscoveryService
                    .get_bank_transaction_endpoints()
                ),

                "bank_transfers": (
                    APIDiscoveryService
                    .get_bank_transfer_endpoints()
                ),

                "bank_statements": (
                    APIDiscoveryService
                    .get_bank_statement_endpoints()
                ),

                "bank_payment_suggestions": (
                    APIDiscoveryService
                    .get_bank_payment_suggestion_endpoints()
                ),

                "warehouses":
                    (
                        APIDiscoveryService
                        .get_warehouse_endpoints()
                    ),

                "inventory":
                    (
                        APIDiscoveryService
                        .get_inventory_endpoints()
                    ),

                "stock_movements":
                    (
                        APIDiscoveryService
                        .get_stock_movement_endpoints()
                    ),

                "stock_transfers":
                    (
                        APIDiscoveryService
                        .get_stock_transfer_endpoints()
                    ),
            },

            "capabilities":
                (
                    APIDiscoveryService
                    .get_capabilities()
                ),
        }


    @staticmethod
    def get_user_endpoints():
        return {
            # ==================================================
            # USER COLLECTION
            # ==================================================

            "list": {
                "methods": [
                    "GET",
                    "POST",
                ],

                "path":
                    "/api/v1/users/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permissions": {
                    "GET":
                        "users.read",

                    "POST":
                        "users.create",
                },

                "query_capabilities": [
                    "filtering",
                    "search",
                    "sorting",
                    "pagination",
                ],

                "status":
                    "available",
            },

            # ==================================================
            # USER DETAIL
            # ==================================================

            "detail": {
                "methods": [
                    "GET",
                    "PATCH",
                ],

                "path":
                    "/api/v1/users/{user_id}/",

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permissions": {
                    "GET":
                        "users.read",

                    "PATCH":
                        "users.update",
                },

                "editable_fields": [
                    "email",
                    "first_name",
                    "last_name",
                    "role_id",
                ],

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },

            "activate": {
                "method":
                    "POST",

                "path":
                    (
                        "/api/v1/users/"
                        "{user_id}/activate/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "users.activate",

                "idempotent":
                    True,

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },
            
            "deactivate": {
                "method":
                    "POST",

                "path":
                    (
                        "/api/v1/users/"
                        "{user_id}/deactivate/"
                    ),

                "authentication_required":
                    True,

                "tenant_scoped":
                    True,

                "permission":
                    "users.deactivate",

                "idempotent":
                    True,

                "self_operation_allowed":
                    False,

                "revokes_sessions":
                    True,

                "last_active_admin_protected":
                    True,

                "cross_tenant_behavior":
                    "not_found",

                "status":
                    "available",
            },
        }