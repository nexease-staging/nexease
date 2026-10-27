import json

from unittest.mock import patch

from django.test import (
    Client,
    SimpleTestCase,
)

from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)
from apps.core.services.mongodb_error_logging_service import (
    MongoDBErrorLoggingService,
)


class APIV1RegressionTestCase(
    SimpleTestCase
):

    def setUp(
        self,
    ):
        # Prevent automated regression tests from
        # creating operational-log documents.

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

    def tearDown(
        self,
    ):
        self.mongodb_log_patcher.stop()
        self.application_log_patcher.stop()

    def assert_api_metadata(
        self,
        response,
    ):
        body = response.json()

        header_request_id = (
            response.headers.get(
                "X-Request-ID"
            )
        )

        body_request_id = body.get(
            "request_id"
        )

        self.assertTrue(
            header_request_id
        )

        self.assertEqual(
            header_request_id,
            body_request_id,
        )

        self.assertEqual(
            body.get(
                "meta",
                {},
            ).get(
                "api_version"
            ),
            "v1",
        )

        self.assertTrue(
            body.get(
                "meta",
                {},
            ).get(
                "response_timestamp"
            )
        )

        self.assertEqual(
            response.headers.get(
                "Cache-Control"
            ),
            "no-store",
        )

    # ==================================================
    # DISCOVERY
    # ==================================================

    def test_api_root_contract(
        self,
    ):
        response = self.client.get(
            "/api/v1/"
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            body[
                "success"
            ]
        )

        self.assertEqual(
            body[
                "data"
            ][
                "api"
            ][
                "name"
            ],
            "django-ims",
        )

        self.assertEqual(
            body[
                "data"
            ][
                "api"
            ][
                "version"
            ],
            "v1",
        )

        self.assertEqual(
            body[
                "data"
            ][
                "capabilities"
            ][
                "tenant_isolation"
            ][
                "client_organization_id_trusted"
            ],
            False,
        )

        self.assert_api_metadata(
            response
        )

    def test_authentication_discovery(
        self,
    ):
        response = self.client.get(
            "/api/v1/auth/"
        )

        body = response.json()

        endpoints = body[
            "data"
        ][
            "endpoints"
        ]

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            endpoints[
                "csrf"
            ][
                "status"
            ],
            "available",
        )

        self.assertEqual(
            endpoints[
                "login"
            ][
                "status"
            ],
            "available",
        )

        self.assertEqual(
            endpoints[
                "logout_all"
            ][
                "status"
            ],
            "available",
        )

        self.assert_api_metadata(
            response
        )

    # ==================================================
    # METHOD PROTECTION
    # ==================================================

    def test_api_root_rejects_post(
        self,
    ):
        response = self.client.post(
            "/api/v1/",
            data=json.dumps({}),
            content_type="application/json",
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertFalse(
            body[
                "success"
            ]
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "METHOD_NOT_ALLOWED",
        )

        self.assert_api_metadata(
            response
        )

    # ==================================================
    # AUTHENTICATION
    # ==================================================

    def test_anonymous_me_is_rejected(
        self,
    ):
        response = self.client.get(
            "/api/v1/auth/me/"
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            401,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "UNAUTHORIZED",
        )

        self.assert_api_metadata(
            response
        )

    # ==================================================
    # CSRF
    # ==================================================

    def test_csrf_bootstrap(
        self,
    ):
        csrf_client = Client(
            enforce_csrf_checks=True,
            raise_request_exception=False,
        )

        response = csrf_client.get(
            "/api/v1/auth/csrf/"
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "csrftoken",
            csrf_client.cookies,
        )

        self.assertEqual(
            body[
                "data"
            ][
                "csrf"
            ][
                "header_name"
            ],
            "X-CSRFToken",
        )

        self.assert_api_metadata(
            response
        )

    def test_login_without_csrf_is_rejected(
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
                        "NotSubmittedToView",
                }
            ),
            content_type="application/json",
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "CSRF_FAILED",
        )

        self.assert_api_metadata(
            response
        )

    # ==================================================
    # CLIENT CORRELATION
    # ==================================================

    def test_valid_client_correlation(
        self,
    ):
        correlation_id = (
            "frontend-regression-12345"
        )

        response = self.client.get(
            "/api/v1/",
            HTTP_X_CORRELATION_ID=(
                correlation_id
            ),
        )

        body = response.json()

        self.assertEqual(
            response.headers.get(
                "X-Correlation-ID"
            ),
            correlation_id,
        )

        self.assertEqual(
            body[
                "meta"
            ][
                "client_correlation_id"
            ],
            correlation_id,
        )

        self.assert_api_metadata(
            response
        )

    def test_client_request_id_is_not_trusted(
        self,
    ):
        supplied_request_id = (
            "client-controlled-request-id"
        )

        response = self.client.get(
            "/api/v1/",
            HTTP_X_REQUEST_ID=(
                supplied_request_id
            ),
        )

        self.assertNotEqual(
            response.headers.get(
                "X-Request-ID"
            ),
            supplied_request_id,
        )

        self.assert_api_metadata(
            response
        )

    # ==================================================
    # RESPONSE CONTRACT
    # ==================================================

    def test_validation_contract(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/_tests/"
                "contract/validation/"
            )
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "details",
            body[
                "error"
            ],
        )

        self.assert_api_metadata(
            response
        )

    def test_conflict_contract(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/_tests/"
                "contract/conflict/"
            )
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            409,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "CONFLICT",
        )

        self.assert_api_metadata(
            response
        )

    def test_business_rule_contract(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/_tests/"
                "contract/unprocessable/"
            )
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            422,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "UNPROCESSABLE_ENTITY",
        )

        self.assert_api_metadata(
            response
        )

    # ==================================================
    # EXCEPTION NORMALIZATION
    # ==================================================

    def test_normalized_validation_exception(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/_tests/"
                "exceptions/validation/"
            )
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "VALIDATION_ERROR",
        )

        self.assert_api_metadata(
            response
        )

    def test_normalized_not_found_exception(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/_tests/"
                "exceptions/not-found/"
            )
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "NOT_FOUND",
        )

        self.assertNotIn(
            "Internal resource detail.",
            str(
                body
            ),
        )

        self.assert_api_metadata(
            response
        )

    def test_normalized_mongodb_exception(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/_tests/"
                "exceptions/mongodb/"
            )
        )

        body = response.json()

        self.assertEqual(
            response.status_code,
            503,
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            "SERVICE_UNAVAILABLE",
        )

        self.assertNotIn(
            "Internal MongoDB timeout detail.",
            str(
                body
            ),
        )

        self.assert_api_metadata(
            response
        )

    def test_unexpected_exception_is_safe(
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

        self.assert_api_metadata(
            response
        )