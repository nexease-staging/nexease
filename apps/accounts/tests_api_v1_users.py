import json

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from django.test import (
    Client,
    SimpleTestCase,
)

from apps.accounts.api.v1.serializers import (
    UserAPISerializer,
)
from apps.accounts.user_management_service import (
    UserCreationValidationError,
    UserManagementService,
    UserUpdateValidationError,
)
from apps.authorization.api_context_service import (
    APIPermissionContextService,
)
from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.services.api_query_pipeline_service import (
    APIQueryPipelineService,
)
from apps.core.services.api_rate_limit_service import (
    APIRateLimitService,
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
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class UserAPIV1RegressionTestCase(
    SimpleTestCase
):

    USERS_URL = "/api/v1/users/"

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Regression Test Organization",
            email="organization@example.com",
            phone="9999999999",
            address="Regression Test Address",
            country="India",
            currency="INR",
            timezone="Asia/Kolkata",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.role = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            name="Admin",
            description="Regression test role.",
            is_active=True,
            permissions=[],
            created_at=now,
            updated_at=now,
        )

        self.actor = self.make_user(
            email="admin@example.com",
            first_name="System",
            last_name="Administrator",
        )

        self.target_user = self.make_user(
            email="employee@example.com",
            first_name="Test",
            last_name="Employee",
        )

        self.organization_context = {
            "user": self.actor,
            "organization": self.organization,
        }

        self.permission_context = {
            "user": self.actor,
            "organization": self.organization,
            "role": self.role,
            "permission_codes": [
                "users.read",
                "users.create",
                "users.update",
                "users.activate",
                "users.deactivate",
            ],
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
                return_value=self.organization_context,
            ),
            patch.object(
                APIPermissionContextService,
                "resolve",
                return_value=self.permission_context,
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
                    lambda response, rate_limit_result:
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

    def make_user(
        self,
        *,
        email,
        first_name,
        last_name,
        is_active=True,
    ):
        now = datetime.utcnow()

        return SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            role=self.role,
            email=email,
            password=(
                "pbkdf2_sha256$test-password-hash"
            ),
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            created_at=now,
            updated_at=now,
            is_authenticated=True,
            is_anonymous=False,
        )

    def detail_url(
        self,
        user=None,
    ):
        user = user or self.target_user

        return (
            f"{self.USERS_URL}"
            f"{user.id}/"
        )

    def activate_url(
        self,
        user=None,
    ):
        user = user or self.target_user

        return (
            f"{self.USERS_URL}"
            f"{user.id}/activate/"
        )

    def deactivate_url(
        self,
        user=None,
    ):
        user = user or self.target_user

        return (
            f"{self.USERS_URL}"
            f"{user.id}/deactivate/"
        )

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

    def test_anonymous_user_list_is_rejected(
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
                self.USERS_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    # ==================================================
    # AUTHORIZATION
    # ==================================================

    def test_user_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.USERS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # LIST
    # ==================================================

    def test_user_list_returns_tenant_users(
        self,
    ):
        pipeline_result = {
            "items": [
                self.actor,
                self.target_user,
            ],
            "pagination": {
                "page": 1,
                "page_size": 25,
                "total_items": 2,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "filters": {},
                "search": None,
                "sort": [
                    "email",
                ],
            },
        }

        with patch.object(
            APITenantQueryService,
            "scope_queryset",
            return_value={
                "queryset": object(),
            },
        ) as tenant_scope_mock, patch.object(
            APIQueryPipelineService,
            "execute",
            return_value=pipeline_result,
        ) as pipeline_mock:
            response = self.client.get(
                self.USERS_URL
            )

        body = self.assert_success_contract(
            response
        )

        users = body["data"]["users"]

        self.assertEqual(
            len(users),
            2,
        )

        self.assertEqual(
            users[1]["email"],
            "employee@example.com",
        )

        tenant_scope_mock.assert_called_once()
        pipeline_mock.assert_called_once()

        serialized_response = json.dumps(
            body
        ).lower()

        self.assertNotIn(
            "password",
            serialized_response,
        )

        self.assertNotIn(
            "pbkdf2",
            serialized_response,
        )

    def test_list_query_parameters_reach_pipeline(
        self,
    ):
        pipeline_result = {
            "items": [],
            "pagination": {
                "page": 2,
                "page_size": 10,
                "total_items": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "filters": {
                    "is_active": True,
                },
                "search": "employee",
                "sort": [
                    "-created_at",
                ],
            },
        }

        with patch.object(
            APITenantQueryService,
            "scope_queryset",
            return_value={
                "queryset": object(),
            },
        ), patch.object(
            APIQueryPipelineService,
            "execute",
            return_value=pipeline_result,
        ) as pipeline_mock:
            response = self.client.get(
                self.USERS_URL,
                {
                    "is_active": "true",
                    "search": "employee",
                    "sort": "-created_at",
                    "page": "2",
                    "page_size": "10",
                },
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["query"]["search"],
            "employee",
        )

        called_request = (
            pipeline_mock
            .call_args
            .args[1]
        )

        self.assertEqual(
            called_request.GET["search"],
            "employee",
        )

        self.assertEqual(
            called_request.GET["page"],
            "2",
        )

    # ==================================================
    # CREATE
    # ==================================================

    def test_create_user_returns_201(
        self,
    ):
        payload = {
            "email":
                "employee@example.com",
            "first_name":
                "Test",
            "last_name":
                "Employee",
            "password":
                "StrongPassword@12345",
            "password_confirmation":
                "StrongPassword@12345",
            "role_id":
                str(self.role.id),
        }

        with patch.object(
            UserManagementService,
            "create_user",
            return_value=self.target_user,
        ) as create_mock:
            response = self.client.post(
                self.USERS_URL,
                data=json.dumps(payload),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        self.assertEqual(
            body["data"]["user"]["email"],
            "employee@example.com",
        )

        serialized_response = json.dumps(
            body
        ).lower()

        self.assertNotIn(
            "password",
            serialized_response,
        )

        create_mock.assert_called_once()

        service_payload = (
            create_mock
            .call_args
            .kwargs["payload"]
        )

        self.assertEqual(
            service_payload,
            payload,
        )

    def test_create_user_validation_error(
        self,
    ):
        validation_error = (
            UserCreationValidationError(
                details={
                    "email": [
                        "Enter a valid email address."
                    ],
                },
            )
        )

        with patch.object(
            UserManagementService,
            "create_user",
            side_effect=validation_error,
        ):
            response = self.client.post(
                self.USERS_URL,
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

    # ==================================================
    # DETAIL AND TENANT ISOLATION
    # ==================================================

    def test_user_detail_returns_user(
        self,
    ):
        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document": self.target_user,
            },
        ) as get_document_mock:
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["user"]["id"],
            str(self.target_user.id),
        )

        self.assertEqual(
            body["data"]["user"]["email"],
            self.target_user.email,
        )

        get_document_mock.assert_called_once()

    def test_cross_tenant_user_is_hidden(
        self,
    ):
        foreign_user_id = ObjectId()

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document": None,
            },
        ) as get_document_mock:
            response = self.client.get(
                (
                    f"{self.USERS_URL}"
                    f"{foreign_user_id}/"
                )
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

        organization_context = (
            get_document_mock
            .call_args
            .kwargs[
                "organization_context"
            ]
        )

        self.assertEqual(
            organization_context,
            self.organization_context,
        )

    # ==================================================
    # UPDATE
    # ==================================================

    def test_update_user_returns_updated_user(
        self,
    ):
        updated_user = self.make_user(
            email="employee@example.com",
            first_name="Updated",
            last_name="Employee",
        )

        updated_user.id = (
            self.target_user.id
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document": self.target_user,
            },
        ), patch.object(
            UserManagementService,
            "update_user",
            return_value=updated_user,
        ) as update_mock:
            response = self.client.patch(
                self.detail_url(),
                data=json.dumps({
                    "first_name": "Updated",
                }),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["user"]["first_name"],
            "Updated",
        )

        update_mock.assert_called_once()

    def test_update_user_validation_error(
        self,
    ):
        validation_error = (
            UserUpdateValidationError(
                details={
                    "role_id": [
                        "You cannot change your own role."
                    ],
                },
            )
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document": self.target_user,
            },
        ), patch.object(
            UserManagementService,
            "update_user",
            side_effect=validation_error,
        ):
            response = self.client.patch(
                self.detail_url(),
                data=json.dumps({
                    "role_id": str(ObjectId()),
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "role_id",
            body["error"]["details"],
        )

    # ==================================================
    # ACTIVATE
    # ==================================================

    def test_activate_user(
        self,
    ):
        inactive_user = self.make_user(
            email="inactive@example.com",
            first_name="Inactive",
            last_name="Employee",
            is_active=False,
        )

        activated_user = self.make_user(
            email="inactive@example.com",
            first_name="Inactive",
            last_name="Employee",
            is_active=True,
        )

        activated_user.id = inactive_user.id

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document": inactive_user,
            },
        ), patch.object(
            UserManagementService,
            "activate_user",
            return_value={
                "user": activated_user,
                "state_changed": True,
            },
        ):
            response = self.client.post(
                self.activate_url(
                    inactive_user
                )
            )

        body = self.assert_success_contract(
            response
        )

        self.assertTrue(
            body["data"]["user"]["is_active"]
        )

        self.assertTrue(
            body["data"]["state_changed"]
        )

    # ==================================================
    # DEACTIVATE
    # ==================================================

    def test_deactivate_user_and_revoke_sessions(
        self,
    ):
        deactivated_user = self.make_user(
            email=self.target_user.email,
            first_name=self.target_user.first_name,
            last_name=self.target_user.last_name,
            is_active=False,
        )

        deactivated_user.id = (
            self.target_user.id
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document": self.target_user,
            },
        ), patch.object(
            UserManagementService,
            "deactivate_user",
            return_value={
                "user": deactivated_user,
                "state_changed": True,
                "sessions_revoked": 2,
            },
        ):
            response = self.client.post(
                self.deactivate_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertFalse(
            body["data"]["user"]["is_active"]
        )

        self.assertTrue(
            body["data"]["state_changed"]
        )

        self.assertEqual(
            body["data"]["sessions_revoked"],
            2,
        )

    # ==================================================
    # METHODS
    # ==================================================

    def test_users_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.USERS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_user_detail_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.detail_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # SERIALIZATION SECURITY
    # ==================================================

    def test_user_serializer_never_exposes_password(
        self,
    ):
        serialized_user = (
            UserAPISerializer
            .serialize_detail(
                self.target_user
            )
        )

        serialized_text = json.dumps(
            serialized_user
        ).lower()

        self.assertNotIn(
            "password",
            serialized_text,
        )

        self.assertNotIn(
            "pbkdf2",
            serialized_text,
        )