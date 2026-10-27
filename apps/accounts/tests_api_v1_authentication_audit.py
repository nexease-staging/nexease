from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from django.test import (
    Client,
    SimpleTestCase,
)

from apps.accounts.authentication_audit_log_service import (
    AuthenticationAuditLogService,
)
from apps.accounts.security_audit_models import (
    AuthenticationAuditLog,
)
from apps.authorization.api_context_service import (
    APIPermissionContextService,
)
from apps.core.services.api_rate_limit_service import (
    APIRateLimitService,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class AuthenticationAuditAPIV1TestCase(
    SimpleTestCase
):

    URL = (
        "/api/v1/auth/"
        "authentication-audit-logs/"
    )

    def setUp(self):
        self.organization = SimpleNamespace(
            id=ObjectId(),
            is_active=True,
        )

        self.other_organization = (
            SimpleNamespace(
                id=ObjectId(),
                is_active=True,
            )
        )

        self.role = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            name="Admin",
            is_active=True,
            permissions=[],
        )

        self.actor = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            role=self.role,
            email="admin@example.com",
            is_active=True,
            is_authenticated=True,
            is_anonymous=False,
            has_permission=(
                lambda code:
                code == "accounting_audit.read"
            ),
        )

        self.organization_context = {
            "user":
                self.actor,

            "organization":
                self.organization,

            "organization_id":
                str(
                    self.organization.id
                ),
        }

        self.permission_context = {
            "user":
                self.actor,

            "organization":
                self.organization,

            "role":
                self.role,

            "permission_codes": [
                "accounting_audit.read",
            ],

            "permissions_by_module": {
                "accounting_audit": [
                    "accounting_audit.read",
                ],
            },
        }

        self.patchers = [
            patch.object(
                APIOrganizationContextService,
                "resolve",
                return_value=(
                    self.organization_context
                ),
            ),

            patch.object(
                APIPermissionContextService,
                "resolve",
                return_value=(
                    self.permission_context
                ),
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
                    lambda response,
                    rate_limit_result:
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

    def make_log(
        self,
        *,
        event_type="LOGIN_SUCCESS",
        identifier="admin@example.com",
        ip_address="127.0.0.1",
        verified=True,
    ):
        log_user = SimpleNamespace(
            id=self.actor.id,
            email=self.actor.email,
        )

        return SimpleNamespace(
            id=ObjectId(),
            event_type=event_type,
            user=log_user,
            organization=self.organization,
            identifier=identifier,
            ip_address=ip_address,
            created_at=datetime.utcnow(),
            integrity_hash="a" * 64,
            verify_integrity=(
                lambda:
                verified
            ),
        )

    def test_unauthenticated_request_returns_401(
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
                self.URL
            )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_wrong_method_returns_405(
        self,
    ):
        response = self.client.post(
            self.URL,
            data={},
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_missing_permission_returns_403(
        self,
    ):
        denied_actor = SimpleNamespace(
            **{
                **self.actor.__dict__,
                "has_permission":
                    lambda code: False,
            }
        )

        denied_context = {
            **self.organization_context,
            "user": denied_actor,
        }

        with patch.object(
            APIOrganizationContextService,
            "resolve",
            return_value=denied_context,
        ):
            response = self.client.get(
                self.URL
            )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_authorized_request_returns_200(
        self,
    ):
        log = self.make_log()

        with patch.object(
            AuthenticationAuditLogService,
            "list_logs",
            return_value=[log],
        ) as mocked_list:
            response = self.client.get(
                self.URL
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertTrue(
            payload["success"]
        )

        self.assertEqual(
            payload["data"]["count"],
            1,
        )

        mocked_list.assert_called_once()

    def test_query_filters_are_forwarded(
        self,
    ):
        with patch.object(
            AuthenticationAuditLogService,
            "list_logs",
            return_value=[],
        ) as mocked_list:
            response = self.client.get(
                self.URL,
                {
                    "event_type":
                        "LOGIN_SUCCESS",

                    "identifier":
                        "admin@example.com",

                    "ip_address":
                        "127.0.0.1",

                    "limit":
                        "25",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        call_kwargs = (
            mocked_list.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["user"],
            self.actor,
        )

        self.assertEqual(
            call_kwargs["organization"],
            self.organization,
        )

        self.assertEqual(
            call_kwargs["event_type"],
            "LOGIN_SUCCESS",
        )

        self.assertEqual(
            call_kwargs["identifier"],
            "admin@example.com",
        )

        self.assertEqual(
            call_kwargs["ip_address"],
            "127.0.0.1",
        )

        self.assertEqual(
            call_kwargs["limit"],
            "25",
        )

    def test_invalid_event_type_returns_validation_error(
        self,
    ):
        with patch.object(
            AuthenticationAuditLogService,
            "list_logs",
            side_effect=ValueError(
                "Invalid event type."
            ),
        ):
            response = self.client.get(
                self.URL,
                {
                    "event_type":
                        "INVALID_EVENT",
                },
            )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_invalid_limit_returns_validation_error(
        self,
    ):
        with patch.object(
            AuthenticationAuditLogService,
            "list_logs",
            side_effect=ValueError(
                "Invalid limit."
            ),
        ):
            response = self.client.get(
                self.URL,
                {
                    "limit": "invalid",
                },
            )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_integrity_status_is_serialized(
        self,
    ):
        log = self.make_log(
            verified=True
        )

        with patch.object(
            AuthenticationAuditLogService,
            "list_logs",
            return_value=[log],
        ):
            response = self.client.get(
                self.URL
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        item = (
            response.json()
            ["data"]
            ["authentication_audit_logs"]
            [0]
        )

        self.assertTrue(
            item["integrity"]["hashed"]
        )

        self.assertTrue(
            item["integrity"]["verified"]
        )

    def test_tampered_integrity_is_reported(
        self,
    ):
        log = self.make_log(
            verified=False
        )

        with patch.object(
            AuthenticationAuditLogService,
            "list_logs",
            return_value=[log],
        ):
            response = self.client.get(
                self.URL
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        item = (
            response.json()
            ["data"]
            ["authentication_audit_logs"]
            [0]
        )

        self.assertFalse(
            item["integrity"]["verified"]
        )

    def test_service_enforces_tenant_isolation(
        self,
    ):
        with self.assertRaisesRegex(
            PermissionError,
            "Organization access denied.",
        ):
            AuthenticationAuditLogService.list_logs(
                user=self.actor,
                organization=(
                    self.other_organization
                ),
            )

    def test_service_enforces_audit_permission(
        self,
    ):
        denied_actor = SimpleNamespace(
            id=self.actor.id,
            organization=self.organization,
            role=self.role,
            email=self.actor.email,
            is_active=True,
            has_permission=(
                lambda code: False
            ),
        )

        with self.assertRaisesRegex(
            PermissionError,
            "Permission denied.",
        ):
            AuthenticationAuditLogService.list_logs(
                user=denied_actor,
                organization=self.organization,
            )