from django.conf import settings
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.test import Client
from django.urls import (
    Resolver404,
    resolve,
)


class Command(
    BaseCommand
):

    help = (
        "Run the final Django IMS API v1 "
        "readiness audit."
    )

    def handle(
        self,
        *args,
        **options,
    ):
        passed = 0
        failed = 0

        def check(
            name,
            condition,
            detail=None,
        ):
            nonlocal passed
            nonlocal failed

            if condition:

                passed += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[PASS] {name}"
                    )
                )

            else:

                failed += 1

                message = (
                    f"[FAIL] {name}"
                )

                if detail:

                    message += (
                        f" — {detail}"
                    )

                self.stdout.write(
                    self.style.ERROR(
                        message
                    )
                )

        # ==================================================
        # SETTINGS
        # ==================================================

        check(
            "Session engine uses MongoDB",
            settings.SESSION_ENGINE
            ==
            (
                "apps.accounts."
                "session_backend"
            ),
        )

        check(
            "Session cookie has expected name",
            settings.SESSION_COOKIE_NAME
            ==
            "ims_sessionid",
        )

        check(
            "Session cookie is HttpOnly",
            settings.SESSION_COOKIE_HTTPONLY
            is True,
        )

        check(
            "CSRF cookie remains frontend-readable",
            settings.CSRF_COOKIE_HTTPONLY
            is False,
        )

        check(
            "Session and CSRF SameSite match",
            settings.SESSION_COOKIE_SAMESITE
            ==
            settings.CSRF_COOKIE_SAMESITE,
        )

        check(
            "Credentialed CORS enabled",
            settings.CORS_ALLOW_CREDENTIALS
            is True,
        )

        check(
            "Wildcard CORS disabled",
            settings.CORS_ALLOW_ALL_ORIGINS
            is False,
        )

        check(
            "Internal API test routes disabled",
            settings
            .ENABLE_INTERNAL_API_TEST_ENDPOINTS
            is False,
        )

        if settings.IS_PRODUCTION:

            check(
                "Production DEBUG disabled",
                settings.DEBUG
                is False,
            )

            check(
                "Production session cookie secure",
                settings.SESSION_COOKIE_SECURE
                is True,
            )

            check(
                "Production CSRF cookie secure",
                settings.CSRF_COOKIE_SECURE
                is True,
            )

            check(
                "Production wildcard hosts rejected",
                "*"
                not in settings.ALLOWED_HOSTS,
            )

        # ==================================================
        # MIDDLEWARE ORDER
        # ==================================================

        middleware = list(
            settings.MIDDLEWARE
        )

        required_middleware = [
            (
                "django.contrib.sessions."
                "middleware.SessionMiddleware"
            ),
            (
                "django.middleware.csrf."
                "CsrfViewMiddleware"
            ),
            (
                "django.contrib.auth."
                "middleware.AuthenticationMiddleware"
            ),
            (
                "apps.accounts.middleware."
                "MongoAuthenticationMiddleware"
            ),
            (
                "apps.core.middleware."
                "request_id_middleware."
                "RequestIDMiddleware"
            ),
            (
                "apps.core.middleware."
                "exception_logging_middleware."
                "ExceptionLoggingMiddleware"
            ),
            (
                "apps.core.middleware."
                "request_logging_middleware."
                "RequestLoggingMiddleware"
            ),
        ]

        all_middleware_present = all(
            middleware_name
            in middleware
            for middleware_name
            in required_middleware
        )

        check(
            "Required middleware present",
            all_middleware_present,
        )

        if all_middleware_present:

            indexes = {
                middleware_name:
                    middleware.index(
                        middleware_name
                    )
                for middleware_name
                in required_middleware
            }

            check(
                "Session runs before CSRF",
                indexes[
                    required_middleware[
                        0
                    ]
                ]
                <
                indexes[
                    required_middleware[
                        1
                    ]
                ],
            )

            check(
                "Django auth runs before Mongo auth",
                indexes[
                    required_middleware[
                        2
                    ]
                ]
                <
                indexes[
                    required_middleware[
                        3
                    ]
                ],
            )

            check(
                (
                    "Request ID runs before "
                    "exception/request logging"
                ),
                (
                    indexes[
                        required_middleware[
                            4
                        ]
                    ]
                    <
                    indexes[
                        required_middleware[
                            5
                        ]
                    ]
                    <
                    indexes[
                        required_middleware[
                            6
                        ]
                    ]
                ),
            )

        # ==================================================
        # ROUTE EXPOSURE
        # ==================================================

        def route_exists(
            path,
        ):
            try:

                resolve(
                    path
                )

                return True

            except Resolver404:

                return False

        check(
            "API root route available",
            route_exists(
                "/api/v1/"
            ),
        )

        check(
            "Authentication root available",
            route_exists(
                "/api/v1/auth/"
            ),
        )

        check(
            "CSRF route available",
            route_exists(
                "/api/v1/auth/csrf/"
            ),
        )

        check(
            "Login route available",
            route_exists(
                "/api/v1/auth/login/"
            ),
        )

        check(
            "Logout route available",
            route_exists(
                "/api/v1/auth/logout/"
            ),
        )

        check(
            "Current-user route available",
            route_exists(
                "/api/v1/auth/me/"
            ),
        )
        check(
            "Logout-all route available",
            route_exists(
                "/api/v1/auth/logout-all/"
            ),
        )

        check(
            "Organization route available",
            route_exists(
                "/api/v1/organization/"
            ),
        )

        check(
            "Users collection route available",
            route_exists(
                "/api/v1/users/"
            ),
        )

        check(
            "User detail route available",
            route_exists(
                "/api/v1/users/audit-user-id/"
            ),
        )

        check(
            "User activation route available",
            route_exists(
                (
                    "/api/v1/users/"
                    "audit-user-id/activate/"
                )
            ),
        )

        check(
            "User deactivation route available",
            route_exists(
                (
                    "/api/v1/users/"
                    "audit-user-id/deactivate/"
                )
            ),
        )

        check(
            "Category-list route available",
            route_exists(
                "/api/v1/categories/"
            ),
        )

        check(
            "Product collection route available",
            route_exists(
                "/api/v1/products/"
            ),
        )

        check(
            "Product detail route available",
            route_exists(
                (
                    "/api/v1/products/"
                    "audit-product-id/"
                )
            ),
        )

        check(
            "Product activation route available",
            route_exists(
                (
                    "/api/v1/products/"
                    "audit-product-id/activate/"
                )
            ),
        )

        check(
            "Product deactivation route available",
            route_exists(
                (
                    "/api/v1/products/"
                    "audit-product-id/deactivate/"
                )
            ),
        )

        check(
            "Customer collection route available",
            route_exists(
                "/api/v1/customers/"
            ),
        )

        check(
            "Customer detail route available",
            route_exists(
                (
                    "/api/v1/customers/"
                    "audit-customer-id/"
                )
            ),
        )

        check(
            "Customer activation route available",
            route_exists(
                (
                    "/api/v1/customers/"
                    "audit-customer-id/activate/"
                )
            ),
        )

        check(
            "Customer deactivation route available",
            route_exists(
                (
                    "/api/v1/customers/"
                    "audit-customer-id/deactivate/"
                )
            ),
        )

        check(
            "Sales Order collection route available",
            route_exists(
                "/api/v1/sales-orders/"
            ),
        )

        check(
            "Sales Order detail route available",
            route_exists(
                (
                    "/api/v1/sales-orders/"
                    "audit-sales-order-id/"
                )
            ),
        )

        check(
            "Sales Order confirmation route available",
            route_exists(
                (
                    "/api/v1/sales-orders/"
                    "audit-sales-order-id/confirm/"
                )
            ),
        )

        check(
            "Sales Order cancellation route available",
            route_exists(
                (
                    "/api/v1/sales-orders/"
                    "audit-sales-order-id/cancel/"
                )
            ),
        )

        check(
            "Sales Order fulfilment route available",
            route_exists(
                (
                    "/api/v1/sales-orders/"
                    "audit-sales-order-id/fulfill/"
                )
            ),
        )
        check(
            "Invoice collection route available",
            route_exists(
                "/api/v1/invoices/"
            ),
        )

        check(
            "Invoice detail route available",
            route_exists(
                (
                    "/api/v1/invoices/"
                    "audit-invoice-id/"
                )
            ),
        )

        check(
            "Invoice issue route available",
            route_exists(
                (
                    "/api/v1/invoices/"
                    "audit-invoice-id/issue/"
                )
            ),
        )

        check(
            "Invoice cancellation route available",
            route_exists(
                (
                    "/api/v1/invoices/"
                    "audit-invoice-id/cancel/"
                )
            ),
        )

        check(
            "Invoice payment route available",
            route_exists(
                (
                    "/api/v1/invoices/"
                    "audit-invoice-id/"
                    "record-payment/"
                )
            ),
        )

        check(
            "Invoice payment-account route available",
            route_exists(
                (
                    "/api/v1/"
                    "invoice-bank-accounts/"
                )
            ),
        )
        check(
            "Sales Return collection route available",
            route_exists(
                "/api/v1/sales-returns/",
            ),
        )

        check(
            "Sales Return detail route available",
            route_exists(
                (
                    "/api/v1/sales-returns/"
                    "audit-sales-return-id/"
                ),
            ),
        )

        check(
            "Sales Return confirmation route available",
            route_exists(
                (
                    "/api/v1/sales-returns/"
                    "audit-sales-return-id/"
                    "confirm/"
                ),
            ),
        )

        check(
            "Sales Return cancellation route available",
            route_exists(
                (
                    "/api/v1/sales-returns/"
                    "audit-sales-return-id/"
                    "cancel/"
                ),
            ),
        )

        check(
            "Credit Note collection route available",
            route_exists(
                "/api/v1/credit-notes/",
            ),
        )

        check(
            "Credit Note detail route available",
            route_exists(
                (
                    "/api/v1/credit-notes/"
                    "audit-credit-note-id/"
                ),
            ),
        )

        check(
            "Credit Note issue route available",
            route_exists(
                (
                    "/api/v1/credit-notes/"
                    "audit-credit-note-id/"
                    "issue/"
                ),
            ),
        )

        check(
            "Credit Note cancellation route available",
            route_exists(
                (
                    "/api/v1/credit-notes/"
                    "audit-credit-note-id/"
                    "cancel/"
                ),
            ),
        )
        check(
            "Customer payment collection route available",
            route_exists(
                (
                    "/api/v1/"
                    "customer-payments/"
                )
            ),
        )

        check(
            "Customer payment detail route available",
            route_exists(
                (
                    "/api/v1/"
                    "customer-payments/"
                    "audit-payment-id/"
                )
            ),
        )

        check(
            "Accounts receivable route available",
            route_exists(
                (
                    "/api/v1/"
                    "accounts-receivable/"
                )
            ),
        )

        check(
            "Receivable aging route available",
            route_exists(
                (
                    "/api/v1/"
                    "accounts-receivable/"
                    "aging/"
                )
            ),
        )
        check(
            "Supplier collection route available",
            route_exists(
                "/api/v1/suppliers/"
            ),
        )

        check(
            "Supplier detail route available",
            route_exists(
                (
                    "/api/v1/suppliers/"
                    "audit-supplier-id/"
                )
            ),
        )

        check(
            "Supplier activation route available",
            route_exists(
                (
                    "/api/v1/suppliers/"
                    "audit-supplier-id/activate/"
                )
            ),
        )

        check(
            "Supplier deactivation route available",
            route_exists(
                (
                    "/api/v1/suppliers/"
                    "audit-supplier-id/deactivate/"
                )
            ),
        )
        check(
            "Purchase Order collection route available",
            route_exists(
                (
                    "/api/v1/"
                    "purchase-orders/"
                )
            ),
        )

        check(
            "Purchase Order detail route available",
            route_exists(
                (
                    "/api/v1/"
                    "purchase-orders/"
                    "audit-purchase-order-id/"
                )
            ),
        )

        check(
            "Purchase Order confirmation route available",
            route_exists(
                (
                    "/api/v1/"
                    "purchase-orders/"
                    "audit-purchase-order-id/"
                    "confirm/"
                )
            ),
        )

        check(
            "Purchase Order cancellation route available",
            route_exists(
                (
                    "/api/v1/"
                    "purchase-orders/"
                    "audit-purchase-order-id/"
                    "cancel/"
                )
            ),
        )
        check(
            "Goods Receipt collection route available",
            route_exists(
                "/api/v1/goods-receipts/",
            ),
        )

        check(
            "Goods Receipt detail route available",
            route_exists(
                (
                    "/api/v1/"
                    "goods-receipts/"
                    "audit-goods-receipt-id/"
                ),
            ),
        )
        check(
            "Purchase Return collection route available",
            route_exists(
                "/api/v1/purchase-returns/",
            ),
        )

        check(
            "Purchase Return detail route available",
            route_exists(
                (
                    "/api/v1/purchase-returns/"
                    "audit-purchase-return-id/"
                ),
            ),
        )

        check(
            "Purchase Return confirmation route available",
            route_exists(
                (
                    "/api/v1/purchase-returns/"
                    "audit-purchase-return-id/"
                    "confirm/"
                ),
            ),
        )

        check(
            "Purchase Return cancellation route available",
            route_exists(
                (
                    "/api/v1/purchase-returns/"
                    "audit-purchase-return-id/"
                    "cancel/"
                ),
            ),
        )

        check(
            "Vendor Debit Note collection route available",
            route_exists(
                "/api/v1/vendor-debit-notes/",
            ),
        )
        check(
            (
                "Chart of Account collection "
                "route available"
            ),
            route_exists(
                "/api/v1/chart-of-accounts/",
            ),
        )

        check(
            (
                "Chart of Account detail "
                "route available"
            ),
            route_exists(
                (
                    "/api/v1/chart-of-accounts/"
                    "audit-account-id/"
                ),
            ),
        )

        check(
            (
                "Chart of Account deactivation "
                "route available"
            ),
            route_exists(
                (
                    "/api/v1/chart-of-accounts/"
                    "audit-account-id/deactivate/"
                ),
            ),
        )

        check(
            (
                "Journal Entry collection "
                "route available"
            ),
            route_exists(
                "/api/v1/journal-entries/",
            ),
        )

        check(
            (
                "Journal Entry detail "
                "route available"
            ),
            route_exists(
                (
                    "/api/v1/journal-entries/"
                    "audit-journal-id/"
                ),
            ),
        )

        check(
            (
                "Journal Entry posting "
                "route available"
            ),
            route_exists(
                (
                    "/api/v1/journal-entries/"
                    "audit-journal-id/post/"
                ),
            ),
        )

        check(
            (
                "Journal Entry reversal "
                "route available"
            ),
            route_exists(
                (
                    "/api/v1/journal-entries/"
                    "audit-journal-id/reverse/"
                ),
            ),
        )

        check(
            "General Ledger route available",
            route_exists(
                (
                    "/api/v1/general-ledger/"
                    "audit-account-id/"
                ),
            ),
        )

        check(
            "Trial Balance route available",
            route_exists(
                "/api/v1/trial-balance/",
            ),
        )
        check(
            "Bank Account collection route available",
            route_exists(
                "/api/v1/bank-accounts/",
            ),
        )

        check(
            "Bank Account detail route available",
            route_exists(
                (
                    "/api/v1/bank-accounts/"
                    "audit-bank-account-id/"
                ),
            ),
        )

        check(
            "Bank Account deactivation route available",
            route_exists(
                (
                    "/api/v1/bank-accounts/"
                    "audit-bank-account-id/"
                    "deactivate/"
                ),
            ),
        )

        check(
            "Bank Transaction collection route available",
            route_exists(
                "/api/v1/bank-transactions/",
            ),
        )

        check(
            "Bank Transaction detail route available",
            route_exists(
                (
                    "/api/v1/bank-transactions/"
                    "audit-transaction-id/"
                ),
            ),
        )

        check(
            "Bank Transaction reconciliation route available",
            route_exists(
                (
                    "/api/v1/bank-transactions/"
                    "audit-transaction-id/"
                    "reconcile/"
                ),
            ),
        )

        check(
            "Bank Transfer collection route available",
            route_exists(
                "/api/v1/bank-transfers/",
            ),
        )

        check(
            "Bank Transfer detail route available",
            route_exists(
                (
                    "/api/v1/bank-transfers/"
                    "audit-transfer-id/"
                ),
            ),
        )

        check(
            "Bank Transfer posting route available",
            route_exists(
                (
                    "/api/v1/bank-transfers/"
                    "audit-transfer-id/"
                    "post/"
                ),
            ),
        )

        check(
            "Bank Transfer cancellation route available",
            route_exists(
                (
                    "/api/v1/bank-transfers/"
                    "audit-transfer-id/"
                    "cancel/"
                ),
            ),
        )
        check(
            "Bank Statement collection route available",
            route_exists(
                "/api/v1/bank-statements/",
            ),
        )

        check(
            "Bank Statement detail route available",
            route_exists(
                (
                    "/api/v1/bank-statements/"
                    "audit-statement-id/"
                ),
            ),
        )

        check(
            "Bank Statement cancellation route available",
            route_exists(
                (
                    "/api/v1/bank-statements/"
                    "audit-statement-id/"
                    "cancel/"
                ),
            ),
        )

        check(
            "Bank Statement auto-match route available",
            route_exists(
                (
                    "/api/v1/bank-statements/"
                    "audit-statement-id/lines/"
                    "1/auto-match/"
                ),
            ),
        )

        check(
            "Bank Statement manual-match route available",
            route_exists(
                (
                    "/api/v1/bank-statements/"
                    "audit-statement-id/lines/"
                    "1/match/"
                ),
            ),
        )

        check(
            "Bank Statement ignore-line route available",
            route_exists(
                (
                    "/api/v1/bank-statements/"
                    "audit-statement-id/lines/"
                    "1/ignore/"
                ),
            ),
        )
        check(
            (
                "Bank Payment Suggestion "
                "collection route available"
            ),
            route_exists(
                (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                ),
            ),
        )

        check(
            (
                "Bank Payment Suggestion "
                "detail route available"
            ),
            route_exists(
                (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "audit-suggestion-id/"
                ),
            ),
        )

        check(
            (
                "Bank Payment Suggestion "
                "generation route available"
            ),
            route_exists(
                (
                    "/api/v1/bank-statements/"
                    "audit-statement-id/lines/"
                    "1/payment-suggestion/"
                ),
            ),
        )

        check(
            (
                "Bank Payment Suggestion "
                "confirmation route available"
            ),
            route_exists(
                (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "audit-suggestion-id/"
                    "confirm/"
                ),
            ),
        )

        check(
            (
                "Bank Payment Suggestion "
                "rejection route available"
            ),
            route_exists(
                (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "audit-suggestion-id/"
                    "reject/"
                ),
            ),
        )

        check(
            (
                "Bank Payment Suggestion "
                "execution route available"
            ),
            route_exists(
                (
                    "/api/v1/"
                    "bank-payment-suggestions/"
                    "audit-suggestion-id/"
                    "execute/"
                ),
            ),
        )
        check(
            "Vendor Debit Note detail route available",
            route_exists(
                (
                    "/api/v1/vendor-debit-notes/"
                    "audit-debit-note-id/"
                ),
            ),
        )

        check(
            "Vendor Debit Note issue route available",
            route_exists(
                (
                    "/api/v1/vendor-debit-notes/"
                    "audit-debit-note-id/"
                    "issue/"
                ),
            ),
        )

        check(
            "Vendor Debit Note cancellation route available",
            route_exists(
                (
                    "/api/v1/vendor-debit-notes/"
                    "audit-debit-note-id/"
                    "cancel/"
                ),
            ),
        )
        check(
            "Warehouse collection route available",
            route_exists(
                "/api/v1/warehouses/"
            ),
        )

        check(
            "Warehouse detail route available",
            route_exists(
                (
                    "/api/v1/warehouses/"
                    "audit-warehouse-id/"
                )
            ),
        )

        check(
            "Warehouse activation route available",
            route_exists(
                (
                    "/api/v1/warehouses/"
                    "audit-warehouse-id/activate/"
                )
            ),
        )

        check(
            "Warehouse deactivation route available",
            route_exists(
                (
                    "/api/v1/warehouses/"
                    "audit-warehouse-id/deactivate/"
                )
            ),
        )

        check(
            "Inventory collection route available",
            route_exists(
                "/api/v1/inventory/"
            ),
        )

        check(
            "Inventory detail route available",
            route_exists(
                (
                    "/api/v1/inventory/"
                    "audit-inventory-id/"
                )
            ),
        )

        check(
            "Inventory adjustment route available",
            route_exists(
                (
                    "/api/v1/inventory/"
                    "audit-inventory-id/adjust/"
                )
            ),
        )

        check(
            "Stock movement collection route available",
            route_exists(
                "/api/v1/stock-movements/"
            ),
        )

        check(
            "Stock movement detail route available",
            route_exists(
                (
                    "/api/v1/stock-movements/"
                    "audit-movement-id/"
                )
            ),
        )

        check(
            "Stock transfer collection route available",
            route_exists(
                "/api/v1/stock-transfers/"
            ),
        )

        check(
            "Stock transfer detail route available",
            route_exists(
                (
                    "/api/v1/stock-transfers/"
                    "audit-transfer-id/"
                )
            ),
        )

        check(
            "Permission-list route available",
            route_exists(
                "/api/v1/permissions/"
            ),
        )

        check(
            "Role collection route available",
            route_exists(
                "/api/v1/roles/"
            ),
        )

        check(
            "Role detail route available",
            route_exists(
                "/api/v1/roles/audit-role-id/"
            ),
        )

        check(
            (
                "Role permission-assignment "
                "route available"
            ),
            route_exists(
                (
                    "/api/v1/roles/"
                    "audit-role-id/permissions/"
                )
            ),
        )

        check(
            "Role activation route available",
            route_exists(
                (
                    "/api/v1/roles/"
                    "audit-role-id/activate/"
                )
            ),
        )

        check(
            "Role deactivation route available",
            route_exists(
                (
                    "/api/v1/roles/"
                    "audit-role-id/deactivate/"
                )
            ),
        )

        check(
            "Internal contract routes hidden",
            not route_exists(
                (
                    "/api/v1/_tests/"
                    "contract/success/"
                )
            ),
        )

        check(
            "Authorization probe hidden",
            not route_exists(
                (
                    "/api/v1/auth/"
                    "authorization-probe/"
                )
            ),
        )

        # ==================================================
        # HTTP CONTRACT
        # ==================================================

        host = (
            settings.ALLOWED_HOSTS[
                0
            ]
            if settings.ALLOWED_HOSTS
            else "testserver"
        )

        if host.startswith(
            "."
        ):

            host = host[
                1:
            ]

        client = Client(
            raise_request_exception=False,
        )

        request_options = {
            "HTTP_HOST":
                host,
        }

        if settings.IS_PRODUCTION:

            request_options[
                "secure"
            ] = True

        api_response = client.get(
            "/api/v1/",
            **request_options,
        )

        check(
            "API root returns 200",
            api_response.status_code
            ==
            200,
            detail=(
                f"status="
                f"{api_response.status_code}"
            ),
        )

        if (
            api_response.status_code
            ==
            200
        ):

            api_body = (
                api_response.json()
            )

            header_request_id = (
                api_response.headers.get(
                    "X-Request-ID"
                )
            )

            check(
                "API response contract succeeds",
                api_body.get(
                    "success"
                )
                is True,
            )

            check(
                "Request ID header/body match",
                bool(
                    header_request_id
                )
                and
                header_request_id
                ==
                api_body.get(
                    "request_id"
                ),
            )

            check(
                "API metadata version is v1",
                api_body.get(
                    "meta",
                    {},
                ).get(
                    "api_version"
                )
                ==
                "v1",
            )

            check(
                "API responses disable caching",
                api_response.headers.get(
                    "Cache-Control"
                )
                ==
                "no-store",
            )

            serialized_manifest = str(
                api_body.get(
                    "data",
                    {}
                )
            )

            check(
                "Discovery hides internal routes",
                "_tests"
                not in serialized_manifest,
            )

            check(
                "Discovery hides authorization probe",
                "authorization-probe"
                not in serialized_manifest,
            )

            manifest_endpoints = (
                api_body.get(
                    "data",
                    {},
                )
                .get(
                    "endpoints",
                    {},
                )
            )

            organization_endpoints = (
                manifest_endpoints.get(
                    "organization",
                    {},
                )
            )

            user_endpoints = (
                manifest_endpoints.get(
                    "users",
                    {},
                )
            )

            category_endpoints = (
                manifest_endpoints.get(
                    "categories",
                    {},
                )
            )

            product_endpoints = (
                manifest_endpoints.get(
                    "products",
                    {},
                )
            )

            customer_endpoints = (
                manifest_endpoints.get(
                    "customers",
                    {},
                )
            )

            sales_order_endpoints = (
                manifest_endpoints.get(
                    "sales_orders",
                    {},
                )
            )

            sales_return_endpoints = (
                manifest_endpoints.get(
                    "sales_returns",
                    {},
                )
            )

            credit_note_endpoints = (
                manifest_endpoints.get(
                    "credit_notes",
                    {},
                )
            )

            invoice_endpoints = (
                manifest_endpoints.get(
                    "invoices",
                    {},
                )
            )
            payment_endpoints = (
                manifest_endpoints.get(
                    "customer_payments",
                    {},
                )
            )

            receivable_endpoints = (
                manifest_endpoints.get(
                    "accounts_receivable",
                    {},
                )
            )
            supplier_endpoints = (
                manifest_endpoints.get(
                    "suppliers",
                    {},
                )
            )
            purchase_order_endpoints = (
                manifest_endpoints.get(
                    "purchase_orders",
                    {},
                )
            )
            goods_receipt_endpoints = (
                manifest_endpoints.get(
                    "goods_receipts",
                    {},
                )
            )
            vendor_bill_endpoints = (
                manifest_endpoints.get(
                    "vendor_bills",
                    {},
                )
            )
            purchase_return_endpoints = (
                manifest_endpoints.get(
                    "purchase_returns",
                    {},
                )
            )
            vendor_debit_note_endpoints = (
                manifest_endpoints.get(
                    "vendor_debit_notes",
                    {},
                )
            )
            chart_of_account_endpoints = (
                manifest_endpoints.get(
                    "chart_of_accounts",
                    {},
                )
            )

            journal_entry_endpoints = (
                manifest_endpoints.get(
                    "journal_entries",
                    {},
                )
            )

            general_ledger_endpoints = (
                manifest_endpoints.get(
                    "general_ledger",
                    {},
                )
            )

            trial_balance_endpoints = (
                manifest_endpoints.get(
                    "trial_balance",
                    {},
                )
            )
            bank_account_endpoints = (
                manifest_endpoints.get(
                    "bank_accounts",
                    {},
                )
            )

            bank_transaction_endpoints = (
                manifest_endpoints.get(
                    "bank_transactions",
                    {},
                )
            )

            bank_transfer_endpoints = (
                manifest_endpoints.get(
                    "bank_transfers",
                    {},
                )
            )

            bank_statement_endpoints = (
                manifest_endpoints.get(
                    "bank_statements",
                    {},
                )
            )

            bank_payment_suggestion_endpoints = (
                manifest_endpoints.get(
                    "bank_payment_suggestions",
                    {},
                )
            )

            warehouse_endpoints = (
                manifest_endpoints.get(
                    "warehouses",
                    {},
                )
            )

            inventory_endpoints = (
                manifest_endpoints.get(
                    "inventory",
                    {},
                )
            )

            movement_endpoints = (
                manifest_endpoints.get(
                    "stock_movements",
                    {},
                )
            )

            transfer_endpoints = (
                manifest_endpoints.get(
                    "stock_transfers",
                    {},
                )
            )
            check(
                (
                    "Discovery exposes Sales Order "
                    "management endpoints"
                ),
                (
                    sales_order_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/sales-orders/"
                    and
                    sales_order_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    sales_order_endpoints
                    .get(
                        "confirm",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    sales_order_endpoints
                    .get(
                        "cancel",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    sales_order_endpoints
                    .get(
                        "fulfill",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    sales_order_endpoints
                    .get(
                        "fulfill",
                        {},
                    )
                    .get(
                        "supports_partial_fulfillment"
                    )
                    is True
                ),
            )
            check(
                (
                    "Discovery exposes Sales Return "
                    "endpoints"
                ),
                all(
                    endpoint_name
                    in sales_return_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "confirm",
                        "cancel",
                    )
                ),
            )

            check(
                (
                    "Discovery documents Sales Return "
                    "lifecycle"
                ),
                (
                    "POST"
                    in sales_return_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "methods",
                        [],
                    )
                    and
                    sales_return_endpoints
                    .get(
                        "confirm",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "sales_returns.confirm"
                    and
                    sales_return_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                ),
            )
            check(
                (
                    "Discovery exposes Credit Note "
                    "endpoints"
                ),
                all(
                    endpoint_name
                    in credit_note_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "issue",
                        "cancel",
                    )
                ),
            )

            check(
                (
                    "Discovery documents Credit Note "
                    "lifecycle"
                ),
                (
                    "POST"
                    in credit_note_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "methods",
                        [],
                    )
                    and
                    credit_note_endpoints
                    .get(
                        "issue",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "credit_notes.issue"
                    and
                    credit_note_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                ),
            )
            check(
                (
                    "Discovery exposes Invoice "
                    "management endpoints"
                ),
                (
                    invoice_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/invoices/"
                    and
                    invoice_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    invoice_endpoints
                    .get(
                        "issue",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    invoice_endpoints
                    .get(
                        "cancel",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    invoice_endpoints
                    .get(
                        "record_payment",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    invoice_endpoints
                    .get(
                        "payment_accounts",
                        {},
                    )
                    .get(
                        "sensitive_account_numbers"
                    )
                    ==
                    "masked"
                ),
            )
            check(
                (
                    "Discovery exposes customer "
                    "payment endpoints"
                ),
                (
                    payment_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    (
                        "/api/v1/"
                        "customer-payments/"
                    )
                    and
                    payment_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "immutable"
                    )
                    is True
                    and
                    payment_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "sensitive_account_numbers"
                    )
                    ==
                    "masked"
                ),
            )

            check(
                (
                    "Discovery exposes accounts "
                    "receivable endpoints"
                ),
                (
                    receivable_endpoints
                    .get(
                        "summary",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    (
                        "/api/v1/"
                        "accounts-receivable/"
                    )
                    and
                    receivable_endpoints
                    .get(
                        "aging",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    receivable_endpoints
                    .get(
                        "aging",
                        {},
                    )
                    .get(
                        "credit_notes_reduce_receivable"
                    )
                    is True
                ),
            )
            check(
                (
                    "Discovery exposes current "
                    "organization endpoint"
                ),
                (
                    organization_endpoints
                    .get(
                        "current",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/organization/"
                    and
                    organization_endpoints
                    .get(
                        "current",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )

            check(
                (
                    "Discovery exposes user "
                    "management endpoints"
                ),


                (
                    user_endpoints
                    .get(
                        "list",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    user_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    user_endpoints
                    .get(
                        "activate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    user_endpoints
                    .get(
                        "deactivate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )

            check(
                (
                    "Discovery exposes product "
                    "category endpoint"
                ),
                (
                    category_endpoints
                    .get(
                        "list",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/categories/"
                    and
                    category_endpoints
                    .get(
                        "list",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )

            check(
                (
                    "Discovery exposes product "
                    "management endpoints"
                ),
                (
                    product_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    product_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    product_endpoints
                    .get(
                        "activate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    product_endpoints
                    .get(
                        "deactivate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    product_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/products/"
                ),
            )
            check(
                (
                    "Discovery exposes customer "
                    "management endpoints"
                ),
                (
                    customer_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/customers/"
                    and
                    customer_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    customer_endpoints
                    .get(
                        "activate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    customer_endpoints
                    .get(
                        "deactivate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )

            check(
                (
                    "Discovery exposes supplier "
                    "management endpoints"
                ),
                (
                    supplier_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/suppliers/"
                    and
                    supplier_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    supplier_endpoints
                    .get(
                        "activate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    supplier_endpoints
                    .get(
                        "deactivate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )
            check(
                (
                    "Discovery exposes Purchase Order "
                    "management endpoints"
                ),
                (
                    purchase_order_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    (
                        "/api/v1/"
                        "purchase-orders/"
                    )
                    and
                    purchase_order_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    purchase_order_endpoints
                    .get(
                        "confirm",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    purchase_order_endpoints
                    .get(
                        "cancel",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    purchase_order_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                ),
            )
            check(
                "Discovery exposes goods receipt endpoints",
                bool(
                    goods_receipt_endpoints
                ),
            )

            check(
                "Discovery documents goods receipt creation",
                (
                    "POST"
                    in goods_receipt_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "methods",
                        [],
                    )
                ),
            )

            check(
                "Discovery documents goods receipt detail",
                (
                    "GET"
                    in goods_receipt_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "methods",
                        [],
                    )
                ),
            )
            check(
                "Discovery exposes Vendor Bill endpoints",
                bool(
                    vendor_bill_endpoints
                ),
            )

            check(
                "Discovery documents Vendor Bill lifecycle",
                all(
                    endpoint_name
                    in vendor_bill_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "post",
                        "cancel",
                    )
                ),
            )

            check(
                "Discovery exposes payable and payment endpoints",
                all(
                    endpoint_name
                    in vendor_bill_endpoints
                    for endpoint_name
                    in (
                        "record_payment",
                        "bank_accounts",
                        "accounts_payable",
                    )
                ),
            )
            check(
                "Vendor Bill collection route available",
                route_exists(
                    "/api/v1/vendor-bills/",
                ),
            )

            check(
                "Vendor Bill detail route available",
                route_exists(
                    (
                        "/api/v1/vendor-bills/"
                        "audit-vendor-bill-id/"
                    ),
                ),
            )

            check(
                "Vendor Bill posting route available",
                route_exists(
                    (
                        "/api/v1/vendor-bills/"
                        "audit-vendor-bill-id/"
                        "post/"
                    ),
                ),
            )

            check(
                "Vendor Bill cancellation route available",
                route_exists(
                    (
                        "/api/v1/vendor-bills/"
                        "audit-vendor-bill-id/"
                        "cancel/"
                    ),
                ),
            )

            check(
                "Vendor Bill payment route available",
                route_exists(
                    (
                        "/api/v1/vendor-bills/"
                        "audit-vendor-bill-id/"
                        "payments/"
                    ),
                ),
            )

            check(
                "Vendor Bill bank-account route available",
                route_exists(
                    (
                        "/api/v1/vendor-bills/"
                        "bank-accounts/"
                    ),
                ),
            )

            check(
                "Accounts payable route available",
                route_exists(
                    "/api/v1/accounts-payable/",
                ),
            )
            check(
                "Discovery exposes Purchase Return endpoints",
                all(
                    endpoint_name
                    in purchase_return_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "confirm",
                        "cancel",
                    )
                ),
            )

            check(
                "Discovery documents Purchase Return creation",
                (
                    "POST"
                    in purchase_return_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "methods",
                        [],
                    )
                    and
                    purchase_return_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                ),
            )

            check(
                "Discovery exposes Vendor Debit Note endpoints",
                all(
                    endpoint_name
                    in vendor_debit_note_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "issue",
                        "cancel",
                    )
                ),
            )
            check(
                (
                    "Discovery exposes Chart of "
                    "Account endpoints"
                ),
                all(
                    endpoint_name
                    in chart_of_account_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "deactivate",
                    )
                ),
            )

            check(
                (
                    "Discovery documents Chart of "
                    "Account protection"
                ),
                (
                    chart_of_account_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                    and
                    "normal_balance"
                    in
                    chart_of_account_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "protected_fields",
                        [],
                    )
                    and
                    chart_of_account_endpoints
                    .get(
                        "deactivate",
                        {},
                    )
                    .get(
                        "system_accounts_protected"
                    )
                    is True
                ),
            )

            check(
                (
                    "Discovery exposes Journal "
                    "Entry endpoints"
                ),
                all(
                    endpoint_name
                    in journal_entry_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "post",
                        "reverse",
                    )
                ),
            )

            check(
                (
                    "Discovery documents Journal "
                    "Entry lifecycle"
                ),
                (
                    journal_entry_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "forced_source_type"
                    )
                    ==
                    "MANUAL"
                    and
                    journal_entry_endpoints
                    .get(
                        "post",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "journal_entries.post"
                    and
                    journal_entry_endpoints
                    .get(
                        "reverse",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "journal_entries.reverse"
                    and
                    journal_entry_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                ),
            )

            check(
                (
                    "Discovery exposes General "
                    "Ledger endpoint"
                ),
                (
                    general_ledger_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    (
                        "/api/v1/general-ledger/"
                        "{account_id}/"
                    )
                    and
                    general_ledger_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "general_ledger.read"
                    and
                    general_ledger_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "posted_journals_only"
                    )
                    is True
                ),
            )

            check(
                (
                    "Discovery exposes Trial "
                    "Balance endpoint"
                ),
                (
                    trial_balance_endpoints
                    .get(
                        "summary",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/trial-balance/"
                    and
                    trial_balance_endpoints
                    .get(
                        "summary",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "trial_balance.read"
                    and
                    trial_balance_endpoints
                    .get(
                        "summary",
                        {},
                    )
                    .get(
                        "posted_journals_only"
                    )
                    is True
                ),
            )
            check(
                "Discovery documents Vendor Debit Note lifecycle",
                (
                    vendor_debit_note_endpoints
                    .get(
                        "issue",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "vendor_debit_notes.issue"
                    and
                    vendor_debit_note_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                ),
            )
            check(
                (
                    "Discovery exposes Bank Account "
                    "management endpoints"
                ),
                (
                    bank_account_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/bank-accounts/"
                    and
                    all(
                        endpoint_name
                        in bank_account_endpoints
                        for endpoint_name
                        in (
                            "collection",
                            "detail",
                            "deactivate",
                        )
                    )
                ),
            )

            check(
                (
                    "Discovery documents Bank Account "
                    "protection"
                ),
                (
                    bank_account_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                    and
                    "current_balance"
                    in
                    bank_account_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "protected_fields",
                        [],
                    )
                ),
            )

            check(
                (
                    "Discovery exposes Bank Transaction "
                    "endpoints"
                ),
                all(
                    endpoint_name
                    in bank_transaction_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "reconcile",
                    )
                ),
            )

            check(
                (
                    "Discovery protects system Bank "
                    "Transaction types"
                ),
                (
                    "TRANSFER_IN"
                    in
                    bank_transaction_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "system_transaction_types",
                        [],
                    )
                    and
                    "TRANSFER_IN"
                    not in
                    bank_transaction_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "manual_transaction_types",
                        [],
                    )
                ),
            )

            check(
                (
                    "Discovery exposes Bank Transfer "
                    "lifecycle"
                ),
                (
                    all(
                        endpoint_name
                        in bank_transfer_endpoints
                        for endpoint_name
                        in (
                            "collection",
                            "detail",
                            "post",
                            "cancel",
                        )
                    )
                    and
                    bank_transfer_endpoints
                    .get(
                        "post",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "bank_transfers.post"
                ),
            )
            check(
                (
                    "Discovery exposes Bank Statement "
                    "endpoints"
                ),
                all(
                    endpoint_name
                    in bank_statement_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "cancel",
                        "auto_match_line",
                        "match_line",
                        "ignore_line",
                    )
                ),
            )

            check(
                (
                    "Discovery documents Bank Statement "
                    "reconciliation"
                ),
                (
                    bank_statement_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/bank-statements/"
                    and
                    bank_statement_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "content_type",
                        {},
                    )
                    .get(
                        "POST"
                    )
                    ==
                    "multipart/form-data"
                    and
                    bank_statement_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                    and
                    bank_statement_endpoints
                    .get(
                        "auto_match_line",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "bank_statements.reconcile"
                    and
                    bank_statement_endpoints
                    .get(
                        "match_line",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "bank_statements.reconcile"
                    and
                    bank_statement_endpoints
                    .get(
                        "ignore_line",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "bank_statements.reconcile"
                ),
            )
            check(
                (
                    "Discovery exposes Bank Payment "
                    "Suggestion endpoints"
                ),
                all(
                    endpoint_name
                    in bank_payment_suggestion_endpoints
                    for endpoint_name
                    in (
                        "collection",
                        "detail",
                        "generate",
                        "confirm",
                        "reject",
                        "execute",
                    )
                ),
            )

            check(
                (
                    "Discovery documents Bank Payment "
                    "Suggestion lifecycle"
                ),
                (
                    bank_payment_suggestion_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    (
                        "/api/v1/"
                        "bank-payment-suggestions/"
                    )
                    and
                    bank_payment_suggestion_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "cross_tenant_behavior"
                    )
                    ==
                    "not_found"
                    and
                    bank_payment_suggestion_endpoints
                    .get(
                        "generate",
                        {},
                    )
                    .get(
                        "permission"
                    )
                    ==
                    "bank_statements.reconcile"
                    and
                    bank_payment_suggestion_endpoints
                    .get(
                        "execute",
                        {},
                    )
                    .get(
                        "compensation_on_failure"
                    )
                    is True
                ),
            )
            check(
                (
                    "Discovery exposes warehouse "
                    "management endpoints"
                ),
                (
                    warehouse_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/warehouses/"
                    and
                    warehouse_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    warehouse_endpoints
                    .get(
                        "activate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    warehouse_endpoints
                    .get(
                        "deactivate",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )

            check(
                (
                    "Discovery exposes inventory "
                    "balance endpoints"
                ),
                (
                    inventory_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/inventory/"
                    and
                    inventory_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                    and
                    inventory_endpoints
                    .get(
                        "adjust",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )

            check(
                (
                    "Discovery exposes immutable "
                    "stock movement endpoints"
                ),
                (
                    movement_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/stock-movements/"
                    and
                    movement_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "immutable"
                    )
                    is True
                    and
                    movement_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )

            check(
                (
                    "Discovery exposes stock "
                    "transfer endpoints"
                ),
                (
                    transfer_endpoints
                    .get(
                        "collection",
                        {},
                    )
                    .get(
                        "path"
                    )
                    ==
                    "/api/v1/stock-transfers/"
                    and
                    transfer_endpoints
                    .get(
                        "detail",
                        {},
                    )
                    .get(
                        "status"
                    )
                    ==
                    "available"
                ),
            )
            check(
                "Users remain inside endpoints",
                (
                    "users"
                    in manifest_endpoints
                    and
                    "users"
                    not in api_body.get(
                        "data",
                        {},
                    )
                ),
            )

            authorization_endpoints = (
                manifest_endpoints.get(
                    "authorization",
                    {},
                )
            )

            required_authorization_endpoints = {
                "permissions",
                "roles",
                "role_detail",
                "role_permissions",
                "role_activate",
                "role_deactivate",
            }

            check(
                (
                    "Discovery exposes authorization "
                    "management endpoints"
                ),
                (
                    required_authorization_endpoints
                    <=
                    set(
                        authorization_endpoints
                    )
                    and
                    all(
                        authorization_endpoints[
                            endpoint_name
                        ].get(
                            "status"
                        )
                        ==
                        "available"

                        for endpoint_name
                        in (
                            required_authorization_endpoints
                        )
                    )
                ),
            )

            check(
                (
                    "Discovery documents protected "
                    "system-role operations"
                ),
                (
                    authorization_endpoints
                    .get(
                        "role_permissions",
                        {},
                    )
                    .get(
                        "system_roles_protected"
                    )
                    is True
                    and
                    authorization_endpoints
                    .get(
                        "role_deactivate",
                        {},
                    )
                    .get(
                        "system_roles_protected"
                    )
                    is True
                    and
                    authorization_endpoints
                    .get(
                        "role_deactivate",
                        {},
                    )
                    .get(
                        "assigned_user_protection"
                    )
                    is True
                ),
            )

        auth_response = client.get(
            "/api/v1/auth/",
            **request_options,
        )

        check(
            "Authentication discovery returns 200",
            auth_response.status_code
            ==
            200,
        )

        csrf_client = Client(
            enforce_csrf_checks=True,
            raise_request_exception=False,
        )

        csrf_response = csrf_client.get(
            "/api/v1/auth/csrf/",
            **request_options,
        )

        check(
            "CSRF bootstrap returns 200",
            csrf_response.status_code
            ==
            200,
        )

        check(
            "CSRF cookie issued",
            settings.CSRF_COOKIE_NAME
            in csrf_client.cookies,
        )

        csrf_failure_response = (
            csrf_client.post(
                "/api/v1/auth/login/",
                data=(
                    '{"email":"audit@example.com",'
                    '"password":"not-sent"}'
                ),
                content_type=(
                    "application/json"
                ),
                **request_options,
            )
        )

        check(
            "Unsafe request without token rejected",
            csrf_failure_response.status_code
            ==
            403,
        )

        try:

            csrf_failure_code = (
                csrf_failure_response.json()
                [
                    "error"
                ][
                    "code"
                ]
            )

        except Exception:

            csrf_failure_code = None

        check(
            "CSRF failure uses API contract",
            csrf_failure_code
            ==
            "CSRF_FAILED",
        )

        anonymous_me = client.get(
            "/api/v1/auth/me/",
            **request_options,
        )

        check(
            "Anonymous current-user request rejected",
            anonymous_me.status_code
            ==
            401,
        )

        try:

            anonymous_code = (
                anonymous_me.json()
                [
                    "error"
                ][
                    "code"
                ]
            )

        except Exception:

            anonymous_code = None

        check(
            "Anonymous error uses API contract",
            anonymous_code
            ==
            "UNAUTHORIZED",
        )

        anonymous_organization = client.get(
            "/api/v1/organization/",
            **request_options,
        )

        check(
            (
                "Anonymous organization request "
                "rejected"
            ),
            anonymous_organization.status_code
            ==
            401,
        )

        try:

            anonymous_organization_code = (
                anonymous_organization.json()
                [
                    "error"
                ][
                    "code"
                ]
            )

        except Exception:

            anonymous_organization_code = None

        check(
            (
                "Anonymous organization error "
                "uses API contract"
            ),
            anonymous_organization_code
            ==
            "UNAUTHORIZED",
        )

        anonymous_users = client.get(
            "/api/v1/users/",
            **request_options,
        )

        check(
            "Anonymous users request rejected",
            anonymous_users.status_code
            ==
            401,
        )

        try:

            anonymous_users_code = (
                anonymous_users.json()
                [
                    "error"
                ][
                    "code"
                ]
            )

        except Exception:

            anonymous_users_code = None

        check(
            (
                "Anonymous users error uses "
                "API contract"
            ),
            anonymous_users_code
            ==
            "UNAUTHORIZED",
        )

        anonymous_permissions = client.get(
            "/api/v1/permissions/",
            **request_options,
        )

        check(
            (
                "Anonymous permission request "
                "rejected"
            ),
            anonymous_permissions.status_code
            ==
            401,
        )

        try:
            anonymous_permissions_code = (
                anonymous_permissions.json()
                [
                    "error"
                ][
                    "code"
                ]
            )

        except Exception:
            anonymous_permissions_code = None

        check(
            (
                "Anonymous permission error "
                "uses API contract"
            ),
            anonymous_permissions_code
            ==
            "UNAUTHORIZED",
        )

        anonymous_roles = client.get(
            "/api/v1/roles/",
            **request_options,
        )

        check(
            "Anonymous role request rejected",
            anonymous_roles.status_code
            ==
            401,
        )

        try:
            anonymous_roles_code = (
                anonymous_roles.json()
                [
                    "error"
                ][
                    "code"
                ]
            )

        except Exception:
            anonymous_roles_code = None

        check(
            (
                "Anonymous role error uses "
                "API contract"
            ),
            anonymous_roles_code
            ==
            "UNAUTHORIZED",
        )
        # ==================================================
        # SUMMARY
        # ==================================================

        total = (
            passed
            +
            failed
        )

        self.stdout.write(
            ""
        )

        self.stdout.write(
            (
                "API v1 readiness summary: "
                f"{passed}/{total} passed, "
                f"{failed} failed."
            )
        )

        if failed:

            raise CommandError(
                (
                    "API v1 readiness audit "
                    "failed."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "API v1 readiness audit "
                    "passed."
                )
            )
        )