import json

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from django.test import (
    Client,
    SimpleTestCase,
)

from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.services.api_rate_limit_service import (
    APIRateLimitService,
)
from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)
from apps.core.services.mongodb_error_logging_service import (
    MongoDBErrorLoggingService,
)
from apps.organizations.api.v1.serializers import (
    OrganizationAPISerializer,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.organizations.services import (
    OrganizationService,
    OrganizationUpdateValidationError,
)


class OrganizationAPIV1RegressionTestCase(
    SimpleTestCase
):

    ORGANIZATION_URL = (
        "/api/v1/organization/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Demo Inventory Company",
            email="organization@example.com",
            phone="+91 9876543210",
            address="Pune, Maharashtra",
            country="India",
            currency="INR",
            timezone="Asia/Kolkata",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.user = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            email="admin@example.com",
            first_name="System",
            last_name="Administrator",
            is_active=True,
            is_authenticated=True,
            is_anonymous=False,
        )

        self.organization_context = {
            "user": self.user,
            "organization": self.organization,
        }

        self.patchers = [
            patch.object(
                ApplicationLoggingService,
                "log",
                return_value=None,
            ),
            patch.object(
                MongoDBErrorLoggingService,
                "log_exception",
                return_value=None,
            ),
            patch.object(
                APIOrganizationContextService,
                "resolve",
                return_value=(
                    self.organization_context
                ),
            ),
            patch.object(
                AuthorizationService,
                "has_permission",
                return_value=True,
            ),
            patch.object(
                APIRateLimitService,
                "check",
                return_value={
                    "allowed": True,
                },
            ),
            patch.object(
                APIRateLimitService,
                "add_headers",
                side_effect=(
                    lambda response, result:
                    response
                ),
            ),
        ]

        for patcher in self.patchers:
            patcher.start()

        self.client = Client(
            raise_request_exception=False
        )

    def tearDown(self):
        for patcher in reversed(
            self.patchers
        ):
            patcher.stop()

    def assert_success_contract(
        self,
        response,
        expected_status=200,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            expected_status,
        )

        self.assertTrue(
            body["success"]
        )

        self.assertIn(
            "data",
            body,
        )

        self.assertTrue(
            body.get("request_id")
        )

        self.assertEqual(
            response.headers.get(
                "X-Request-ID"
            ),
            body["request_id"],
        )

        self.assertEqual(
            response.headers.get(
                "Cache-Control"
            ),
            "no-store",
        )

        return body

    def assert_error_contract(
        self,
        response,
        expected_status,
        expected_code,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            expected_status,
        )

        self.assertFalse(
            body["success"]
        )

        self.assertEqual(
            body["error"]["code"],
            expected_code,
        )

        self.assertTrue(
            body.get("request_id")
        )

        return body

    # ==================================================
    # AUTHENTICATION
    # ==================================================

    def test_anonymous_request_is_rejected(
        self,
    ):
        with patch.object(
            APIOrganizationContextService,
            "resolve",
            side_effect=PermissionError(
                "Not authenticated."
            ),
        ):
            response = self.client.get(
                self.ORGANIZATION_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    # ==================================================
    # CURRENT ORGANIZATION
    # ==================================================

    def test_current_organization_is_returned(
        self,
    ):
        response = self.client.get(
            self.ORGANIZATION_URL
        )

        body = self.assert_success_contract(
            response
        )

        organization = (
            body["data"]["organization"]
        )

        self.assertEqual(
            organization["id"],
            str(self.organization.id),
        )

        self.assertEqual(
            organization["name"],
            "Demo Inventory Company",
        )

        self.assertEqual(
            organization["currency"],
            "INR",
        )

        self.assertEqual(
            organization["timezone"],
            "Asia/Kolkata",
        )

    def test_client_organization_id_is_ignored(
        self,
    ):
        foreign_organization_id = (
            ObjectId()
        )

        response = self.client.get(
            self.ORGANIZATION_URL,
            {
                "organization_id": (
                    str(
                        foreign_organization_id
                    )
                ),
            },
        )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body[
                "data"
            ][
                "organization"
            ][
                "id"
            ],
            str(self.organization.id),
        )

        self.assertNotEqual(
            body[
                "data"
            ][
                "organization"
            ][
                "id"
            ],
            str(foreign_organization_id),
        )

    # ==================================================
    # AUTHORIZATION
    # ==================================================

    def test_update_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.patch(
                self.ORGANIZATION_URL,
                data=json.dumps({
                    "name": "Updated Company",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # UPDATE
    # ==================================================

    def test_organization_can_be_updated(
        self,
    ):
        updated_organization = (
            SimpleNamespace(
                **vars(self.organization)
            )
        )

        updated_organization.name = (
            "Updated Inventory Company"
        )

        updated_organization.currency = (
            "USD"
        )

        payload = {
            "name":
                "Updated Inventory Company",
            "currency":
                "USD",
        }

        with patch.object(
            OrganizationService,
            "update_organization",
            return_value=(
                updated_organization
            ),
        ) as update_mock:
            response = self.client.patch(
                self.ORGANIZATION_URL,
                data=json.dumps(payload),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        organization = (
            body["data"]["organization"]
        )

        self.assertEqual(
            organization["name"],
            "Updated Inventory Company",
        )

        self.assertEqual(
            organization["currency"],
            "USD",
        )

        update_mock.assert_called_once_with(
            organization=self.organization,
            payload=payload,
        )

    def test_update_validation_error_uses_contract(
        self,
    ):
        error = (
            OrganizationUpdateValidationError(
                details={
                    "email": [
                        (
                            "Enter a valid "
                            "email address."
                        )
                    ],
                },
            )
        )

        with patch.object(
            OrganizationService,
            "update_organization",
            side_effect=error,
        ):
            response = self.client.patch(
                self.ORGANIZATION_URL,
                data=json.dumps({
                    "email": "invalid",
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "email",
            body["error"]["details"],
        )

    def test_update_requires_json_content_type(
        self,
    ):
        response = self.client.patch(
            self.ORGANIZATION_URL,
            data="name=Updated",
            content_type=(
                "application/x-www-form-urlencoded"
            ),
        )

        self.assert_error_contract(
            response,
            400,
            "BAD_REQUEST",
        )

    def test_invalid_json_is_rejected(
        self,
    ):
        response = self.client.patch(
            self.ORGANIZATION_URL,
            data="{invalid-json",
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            400,
            "BAD_REQUEST",
        )

    def test_missing_organization_returns_not_found(
        self,
    ):
        with patch.object(
            OrganizationService,
            "update_organization",
            side_effect=LookupError(
                "Organization not found."
            ),
        ):
            response = self.client.patch(
                self.ORGANIZATION_URL,
                data=json.dumps({
                    "name": "Updated Company",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    # ==================================================
    # METHODS
    # ==================================================

    def test_post_is_not_allowed(
        self,
    ):
        response = self.client.post(
            self.ORGANIZATION_URL,
            data=json.dumps({
                "name": "New Organization",
            }),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_delete_is_not_allowed(
        self,
    ):
        response = self.client.delete(
            self.ORGANIZATION_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # SERVICE VALIDATION
    # ==================================================

    def test_service_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            OrganizationUpdateValidationError
        ) as context:
            (
                OrganizationService
                .validate_update_payload({
                    "is_active": False,
                })
            )

        self.assertIn(
            "is_active",
            context.exception.details,
        )

    def test_service_normalizes_valid_payload(
        self,
    ):
        result = (
            OrganizationService
            .validate_update_payload({
                "name":
                    "  Updated Company  ",
                "email":
                    "  ADMIN@EXAMPLE.COM  ",
                "phone":
                    " +91 9876543210 ",
                "address":
                    "  Pune, India  ",
                "country":
                    "  India  ",
                "currency":
                    " usd ",
                "timezone":
                    "Asia/Kolkata",
            })
        )

        self.assertEqual(
            result["name"],
            "Updated Company",
        )

        self.assertEqual(
            result["email"],
            "admin@example.com",
        )

        self.assertEqual(
            result["phone"],
            "+91 9876543210",
        )

        self.assertEqual(
            result["address"],
            "Pune, India",
        )

        self.assertEqual(
            result["currency"],
            "USD",
        )

    # ==================================================
    # SERIALIZATION
    # ==================================================

    def test_serializer_has_expected_fields(
        self,
    ):
        serialized = (
            OrganizationAPISerializer
            .serialize_detail(
                self.organization
            )
        )

        self.assertEqual(
            set(serialized.keys()),
            {
                "business_scope",
                "id",
                "name",
                "country",
                "currency",
                "timezone",
                "is_active",
                "email",
                "phone",
                "address",
                "created_at",
                "updated_at",
            },
        )

        self.assertNotIn(
            "password",
            serialized,
        )

        self.assertNotIn(
            "database",
            serialized,
        )
        