import json

from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from django.conf import settings
from django.test import (
    Client,
    RequestFactory,
    SimpleTestCase,
)

from apps.authorization.models import (
    Permission,
    Role,
)
from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.services.api_filtering_service import (
    APIFilteringError,
    APIFilteringService,
)
from apps.core.services.api_pagination_service import (
    APIPaginationError,
    APIPaginationService,
)
from apps.core.services.api_serialization_service import (
    APISerializationError,
    APISerializationService,
)
from apps.core.services.api_sorting_service import (
    APISortingError,
    APISortingService,
)
from apps.core.services.api_tenant_query_service import (
    APITenantQueryService,
)
from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)
from apps.core.services.mongodb_error_logging_service import (
    MongoDBErrorLoggingService,
)
from apps.organizations.models import (
    Organization,
)


class APIV1SecurityRegressionTestCase(
    SimpleTestCase
):

    def setUp(
        self,
    ):
        self.application_log_patcher = (
            patch.object(
                ApplicationLoggingService,
                "log",
                return_value=None,
            )
        )

        self.mongodb_log_patcher = (
            patch.object(
                MongoDBErrorLoggingService,
                "log_exception",
                return_value=None,
            )
        )

        self.application_log_patcher.start()
        self.mongodb_log_patcher.start()

        self.client = Client(
            raise_request_exception=False
        )

        self.factory = RequestFactory()

    def tearDown(
        self,
    ):
        self.mongodb_log_patcher.stop()
        self.application_log_patcher.stop()

    # ==================================================
    # SECURITY HEADERS
    # ==================================================

    def test_api_security_headers(
        self,
    ):
        response = self.client.get(
            "/api/v1/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.headers.get(
                "Cache-Control"
            ),
            "no-store",
        )

        self.assertEqual(
            response.headers.get(
                "X-Content-Type-Options"
            ),
            "nosniff",
        )

        self.assertEqual(
            response.headers.get(
                "X-Frame-Options"
            ),
            "DENY",
        )

        self.assertEqual(
            response.headers.get(
                "Referrer-Policy"
            ),
            "strict-origin-when-cross-origin",
        )

        self.assertIn(
            "camera=()",
            response.headers.get(
                "Permissions-Policy",
                "",
            ),
        )

    # ==================================================
    # CORS
    # ==================================================

    def test_untrusted_cors_origin_is_rejected(
        self,
    ):
        response = self.client.get(
            "/api/v1/",
            HTTP_ORIGIN=(
                "https://evil.example"
            ),
        )

        self.assertIsNone(
            response.headers.get(
                "Access-Control-Allow-Origin"
            )
        )

    # ==================================================
    # REQUEST CORRELATION
    # ==================================================

    def test_client_request_id_is_not_trusted(
        self,
    ):
        supplied_id = (
            "attacker-controlled-request-id"
        )

        response = self.client.get(
            "/api/v1/",
            HTTP_X_REQUEST_ID=(
                supplied_id
            ),
        )

        generated_id = (
            response.headers.get(
                "X-Request-ID"
            )
        )

        self.assertTrue(
            generated_id
        )

        self.assertNotEqual(
            generated_id,
            supplied_id,
        )

        self.assertEqual(
            generated_id,
            response.json().get(
                "request_id"
            ),
        )

    def test_invalid_correlation_id_is_ignored(
        self,
    ):
        response = self.client.get(
            "/api/v1/",
            HTTP_X_CORRELATION_ID=(
                "invalid correlation with spaces"
            ),
        )

        self.assertIsNone(
            response.headers.get(
                "X-Correlation-ID"
            )
        )

        self.assertNotIn(
            "client_correlation_id",
            response.json().get(
                "meta",
                {},
            ),
        )

    # ==================================================
    # CSRF
    # ==================================================

    def test_unsafe_request_requires_csrf(
        self,
    ):
        csrf_client = Client(
            enforce_csrf_checks=True,
            raise_request_exception=False,
        )

        response = csrf_client.post(
            "/api/v1/auth/login/",
            data=json.dumps(
                {
                    "email":
                        "admin@example.com",

                    "password":
                        "request-must-not-reach-view",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.json()[
                "error"
            ][
                "code"
            ],
            "CSRF_FAILED",
        )

    # ==================================================
    # AUTHENTICATION AND AUTHORIZATION
    # ==================================================

    def test_anonymous_current_user_is_rejected(
        self,
    ):
        response = self.client.get(
            "/api/v1/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

        self.assertEqual(
            response.json()[
                "error"
            ][
                "code"
            ],
            "UNAUTHORIZED",
        )

    def test_authorization_probe_is_not_exposed(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/auth/"
                "authorization-probe/"
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )
        
    def test_cross_tenant_role_is_denied(
        self,
    ):
        organization_one = Organization(
            id=ObjectId(),
            name="Organization One",
            is_active=True,
        )

        organization_two = Organization(
            id=ObjectId(),
            name="Organization Two",
            is_active=True,
        )

        role = SimpleNamespace(
            id=ObjectId(),
            is_active=True,
            organization=(
                organization_two
            ),
            _data={
                "permissions":
                    [],
            },
        )

        user = SimpleNamespace(
            is_active=True,
            organization=(
                organization_one
            ),
            role=role,
        )

        self.assertFalse(
            AuthorizationService
            .has_permission(
                user,
                "products.read",
            )
        )

    # ==================================================
    # TENANT ISOLATION
    # ==================================================

    def test_client_organization_id_is_ignored(
        self,
    ):
        trusted_organization = Organization(
            id=ObjectId(),
            name="Trusted Organization",
            is_active=True,
        )

        request = self.factory.get(
            "/api/v1/test/",
            {
                "organization_id":
                    "000000000000000000000000",
            },
        )

        result = (
            APITenantQueryService
            .scope_queryset(
                Role.objects.all(),
                request,
                organization_context={
                    "user":
                        object(),

                    "organization":
                        trusted_organization,

                    "organization_id":
                        str(
                            trusted_organization.id
                        ),
                },
            )
        )

        self.assertEqual(
            result[
                "organization_id"
            ],
            str(
                trusted_organization.id
            ),
        )

        self.assertNotEqual(
            result[
                "organization_id"
            ],
            "000000000000000000000000",
        )

    # ==================================================
    # QUERY INJECTION
    # ==================================================

    def test_filter_operator_injection_is_rejected(
        self,
    ):
        request = self.factory.get(
            "/api/v1/test/",
            {
                "$where":
                    "malicious",
            },
        )

        with self.assertRaises(
            APIFilteringError
        ):

            APIFilteringService.apply(
                Permission.objects.all(),
                request,
                allowed_filters={
                    "module": {
                        "field":
                            "module",

                        "lookup":
                            "iexact",

                        "parser":
                            "string",
                    },
                },
            )

    def test_sort_operator_injection_is_rejected(
        self,
    ):
        request = self.factory.get(
            "/api/v1/test/",
            {
                "sort":
                    "$natural",
            },
        )

        with self.assertRaises(
            APISortingError
        ):

            APISortingService.apply(
                Permission.objects.all(),
                request,
                allowed_fields={
                    "code":
                        "code",
                },
                default_sort=[
                    "code",
                ],
            )

    def test_oversized_page_is_rejected(
        self,
    ):
        request = self.factory.get(
            "/api/v1/test/",
            {
                "page_size":
                    "101",
            },
        )

        with self.assertRaises(
            APIPaginationError
        ):

            APIPaginationService.parse(
                request
            )

    # ==================================================
    # SERIALIZATION
    # ==================================================

    def test_mongoengine_document_cannot_leak(
        self,
    ):
        permission = Permission(
            code="security.test",
            name="Security Test",
            module="security",
        )

        with self.assertRaises(
            APISerializationError
        ):

            APISerializationService.serialize_value(
                permission
            )

    # ==================================================
    # SAFE ERRORS
    # ==================================================

    def test_unexpected_exception_hides_details(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/_tests/"
                "exceptions/unexpected/"
            )
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            500,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "INTERNAL_ERROR",
        )

        self.assertNotIn(
            "Sensitive internal exception detail.",
            str(
                body
            ),
        )

        self.assertNotIn(
            "traceback",
            str(
                body
            ).lower(),
        )

    # ==================================================
    # DISCOVERY EXPOSURE
    # ==================================================

    def test_discovery_does_not_expose_test_routes(
        self,
    ):
        response = self.client.get(
            "/api/v1/"
        )

        serialized_body = json.dumps(
            response.json()
        )

        self.assertNotIn(
            "_tests",
            serialized_body,
        )

    # ==================================================
    # COOKIE SETTINGS
    # ==================================================

    def test_cookie_security_settings(
        self,
    ):
        self.assertTrue(
            settings
            .SESSION_COOKIE_HTTPONLY
        )

        self.assertFalse(
            settings
            .CSRF_COOKIE_HTTPONLY
        )

        self.assertIn(
            settings
            .SESSION_COOKIE_SAMESITE,
            {
                "Lax",
                "Strict",
                "None",
            },
        )

        self.assertEqual(
            settings
            .CSRF_COOKIE_SAMESITE,
            settings
            .SESSION_COOKIE_SAMESITE,
        )

        self.assertTrue(
            settings
            .CORS_ALLOW_CREDENTIALS
        )

        self.assertFalse(
            settings
            .CORS_ALLOW_ALL_ORIGINS
        )

        if settings.IS_PRODUCTION:

            self.assertTrue(
                settings
                .SESSION_COOKIE_SECURE
            )

            self.assertTrue(
                settings
                .CSRF_COOKIE_SECURE
            )