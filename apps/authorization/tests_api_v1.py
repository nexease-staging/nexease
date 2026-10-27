import json

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from django.test import (
    Client,
    SimpleTestCase,
)

from apps.authorization.api_context_service import (
    APIPermissionContextService,
)
from apps.authorization.role_management_service import (
    RoleManagementService,
    RoleStateValidationError,
    RoleValidationError,
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


class AuthorizationAPIV1RegressionTestCase(
    SimpleTestCase
):

    PERMISSIONS_URL = (
        "/api/v1/permissions/"
    )

    ROLES_URL = (
        "/api/v1/roles/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Regression Organization",
            is_active=True,
        )

        self.permission = SimpleNamespace(
            id=ObjectId(),
            code="products.read",
            name="View Products",
            description="Allows viewing products.",
            module="products",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.second_permission = (
            SimpleNamespace(
                id=ObjectId(),
                code="users.read",
                name="View Users",
                description=(
                    "Allows viewing users."
                ),
                module="users",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )

        self.actor_role = self.make_role(
            name="Admin",
            is_system=True,
            permissions=[
                self.permission,
                self.second_permission,
            ],
        )

        self.actor = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            role=self.actor_role,
            email="admin@example.com",
            first_name="System",
            last_name="Administrator",
            is_active=True,
            is_authenticated=True,
            is_anonymous=False,
        )

        self.custom_role = self.make_role(
            name="Custom Manager",
            is_system=False,
            permissions=[
                self.permission,
            ],
        )

        self.organization_context = {
            "user":
                self.actor,

            "organization":
                self.organization,
        }

        self.permission_context = {
            "user":
                self.actor,

            "organization":
                self.organization,

            "role":
                self.actor_role,

            "permission_codes": [
                "permissions.read",
                "roles.read",
                "roles.create",
                "roles.update",
                "roles.assign_permissions",
                "roles.activate",
                "roles.deactivate",
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

    def make_role(
        self,
        *,
        name,
        is_system,
        permissions,
        is_active=True,
    ):
        now = datetime.utcnow()

        return SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            name=name,
            description=(
                f"{name} description."
            ),
            is_system=is_system,
            permissions=permissions,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )

    def role_detail_url(
        self,
        role=None,
    ):
        role = role or self.custom_role

        return (
            f"{self.ROLES_URL}"
            f"{role.id}/"
        )

    def role_permissions_url(
        self,
        role=None,
    ):
        role = role or self.custom_role

        return (
            f"{self.ROLES_URL}"
            f"{role.id}/permissions/"
        )

    def role_activate_url(
        self,
        role=None,
    ):
        role = role or self.custom_role

        return (
            f"{self.ROLES_URL}"
            f"{role.id}/activate/"
        )

    def role_deactivate_url(
        self,
        role=None,
    ):
        role = role or self.custom_role

        return (
            f"{self.ROLES_URL}"
            f"{role.id}/deactivate/"
        )

    def assert_success(
        self,
        response,
        status=200,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            status,
        )

        self.assertTrue(
            body["success"]
        )

        self.assertTrue(
            body.get(
                "request_id"
            )
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

    def assert_error(
        self,
        response,
        status,
        code=None,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            status,
        )

        self.assertFalse(
            body["success"]
        )

        if code is not None:
            self.assertEqual(
                body["error"]["code"],
                code,
            )

        self.assertTrue(
            body.get(
                "request_id"
            )
        )

        return body

    # ==================================================
    # PERMISSIONS
    # ==================================================

    def test_anonymous_permission_list_is_rejected(
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
                self.PERMISSIONS_URL
            )

        self.assert_error(
            response,
            401,
            "UNAUTHORIZED",
        )

    def test_permission_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.PERMISSIONS_URL
            )

        self.assert_error(
            response,
            403,
            "FORBIDDEN",
        )

    def test_permission_list_returns_permissions(
        self,
    ):
        pipeline_result = {
            "items": [
                self.permission,
                self.second_permission,
            ],

            "pagination": {
                "page": 1,
                "page_size": 50,
                "total_items": 2,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },

            "query": {
                "filters": {},
                "search": None,
                "sort": [
                    "module",
                    "code",
                ],
            },
        }

        with patch.object(
            APIQueryPipelineService,
            "execute",
            return_value=pipeline_result,
        ):
            response = self.client.get(
                self.PERMISSIONS_URL
            )

        body = self.assert_success(
            response
        )

        self.assertEqual(
            len(
                body[
                    "data"
                ][
                    "permissions"
                ]
            ),
            2,
        )

        self.assertEqual(
            body[
                "data"
            ][
                "modules"
            ],
            [
                "products",
                "users",
            ],
        )

    # ==================================================
    # ROLE COLLECTION
    # ==================================================

    def test_role_list_returns_tenant_roles(
        self,
    ):
        pipeline_result = {
            "items": [
                self.actor_role,
                self.custom_role,
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
                    "name",
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
        ):
            response = self.client.get(
                self.ROLES_URL
            )

        body = self.assert_success(
            response
        )

        self.assertEqual(
            len(
                body["data"]["roles"]
            ),
            2,
        )

    def test_create_custom_role(
        self,
    ):
        payload = {
            "name":
                "Custom Manager",

            "description":
                "Custom role.",

            "permission_codes": [
                "products.read",
            ],
        }

        with patch.object(
            RoleManagementService,
            "create_role",
            return_value=self.custom_role,
        ) as create_mock:
            response = self.client.post(
                self.ROLES_URL,
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success(
            response,
            201,
        )

        self.assertEqual(
            body[
                "data"
            ][
                "role"
            ][
                "name"
            ],
            "Custom Manager",
        )

        create_mock.assert_called_once()

    def test_create_role_validation_error(
        self,
    ):
        error = RoleValidationError(
            details={
                "name": [
                    "name is required."
                ],
            },
        )

        with patch.object(
            RoleManagementService,
            "create_role",
            side_effect=error,
        ):
            response = self.client.post(
                self.ROLES_URL,
                data=json.dumps({
                    "name": "",
                }),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_error(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "name",
            body["error"]["details"],
        )

    # ==================================================
    # ROLE DETAIL
    # ==================================================

    def test_role_detail_returns_role(
        self,
    ):
        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    self.custom_role,
            },
        ):
            response = self.client.get(
                self.role_detail_url()
            )

        body = self.assert_success(
            response
        )

        role = body[
            "data"
        ][
            "role"
        ]

        self.assertEqual(
            role["id"],
            str(
                self.custom_role.id
            ),
        )

        self.assertEqual(
            role["permission_codes"],
            [
                "products.read",
            ],
        )

    def test_cross_tenant_role_is_hidden(
        self,
    ):
        foreign_role_id = ObjectId()

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document": None,
            },
        ):
            response = self.client.get(
                (
                    f"{self.ROLES_URL}"
                    f"{foreign_role_id}/"
                )
            )

        self.assert_error(
            response,
            404,
            "NOT_FOUND",
        )

    def test_update_custom_role(
        self,
    ):
        updated_role = self.make_role(
            name="Updated Manager",
            is_system=False,
            permissions=[
                self.permission,
            ],
        )

        updated_role.id = (
            self.custom_role.id
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    self.custom_role,
            },
        ), patch.object(
            RoleManagementService,
            "update_role",
            return_value=updated_role,
        ):
            response = self.client.patch(
                self.role_detail_url(),
                data=json.dumps({
                    "name":
                        "Updated Manager",
                }),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success(
            response
        )

        self.assertEqual(
            body[
                "data"
            ][
                "role"
            ][
                "name"
            ],
            "Updated Manager",
        )

    def test_system_role_update_is_rejected(
        self,
    ):
        error = (
            RoleStateValidationError(
                message=(
                    "System roles cannot "
                    "be modified."
                ),
                details={
                    "role": [
                        "System role protected."
                    ],
                },
            )
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    self.actor_role,
            },
        ), patch.object(
            RoleManagementService,
            "update_role",
            side_effect=error,
        ):
            response = self.client.patch(
                self.role_detail_url(
                    self.actor_role
                ),
                data=json.dumps({
                    "name":
                        "Changed Admin",
                }),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_error(
            response,
            422,
        )

        self.assertIn(
            "role",
            body["error"]["details"],
        )

    # ==================================================
    # PERMISSION ASSIGNMENT
    # ==================================================

    def test_assign_role_permissions(
        self,
    ):
        updated_role = self.make_role(
            name="Custom Manager",
            is_system=False,
            permissions=[
                self.permission,
                self.second_permission,
            ],
        )

        updated_role.id = (
            self.custom_role.id
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    self.custom_role,
            },
        ), patch.object(
            RoleManagementService,
            "assign_permissions",
            return_value=updated_role,
        ):
            response = self.client.patch(
                self.role_permissions_url(),
                data=json.dumps({
                    "permission_codes": [
                        "products.read",
                        "users.read",
                    ],
                }),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success(
            response
        )

        self.assertEqual(
            body[
                "data"
            ][
                "role"
            ][
                "permission_count"
            ],
            2,
        )

    def test_system_role_permissions_are_protected(
        self,
    ):
        error = (
            RoleStateValidationError(
                message=(
                    "System-role permissions "
                    "cannot be modified."
                ),
                details={
                    "role": [
                        "System role protected."
                    ],
                },
            )
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    self.actor_role,
            },
        ), patch.object(
            RoleManagementService,
            "assign_permissions",
            side_effect=error,
        ):
            response = self.client.patch(
                self.role_permissions_url(
                    self.actor_role
                ),
                data=json.dumps({
                    "permission_codes": [],
                }),
                content_type=(
                    "application/json"
                ),
            )

        self.assert_error(
            response,
            422,
        )

    # ==================================================
    # ROLE STATE
    # ==================================================

    def test_activate_role(
        self,
    ):
        inactive_role = self.make_role(
            name="Inactive Role",
            is_system=False,
            permissions=[],
            is_active=False,
        )

        active_role = self.make_role(
            name="Inactive Role",
            is_system=False,
            permissions=[],
            is_active=True,
        )

        active_role.id = (
            inactive_role.id
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    inactive_role,
            },
        ), patch.object(
            RoleManagementService,
            "activate_role",
            return_value={
                "role":
                    active_role,

                "state_changed":
                    True,
            },
        ):
            response = self.client.post(
                self.role_activate_url(
                    inactive_role
                )
            )

        body = self.assert_success(
            response
        )

        self.assertTrue(
            body[
                "data"
            ][
                "state_changed"
            ]
        )

    def test_deactivate_custom_role(
        self,
    ):
        inactive_role = self.make_role(
            name=self.custom_role.name,
            is_system=False,
            permissions=[
                self.permission,
            ],
            is_active=False,
        )

        inactive_role.id = (
            self.custom_role.id
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    self.custom_role,
            },
        ), patch.object(
            RoleManagementService,
            "deactivate_role",
            return_value={
                "role":
                    inactive_role,

                "state_changed":
                    True,

                "assigned_active_users":
                    0,
            },
        ):
            response = self.client.post(
                self.role_deactivate_url()
            )

        body = self.assert_success(
            response
        )

        self.assertFalse(
            body[
                "data"
            ][
                "role"
            ][
                "is_active"
            ]
        )

    def test_protected_role_deactivation_is_rejected(
        self,
    ):
        error = (
            RoleStateValidationError(
                message=(
                    "System roles cannot "
                    "be deactivated."
                ),
                details={
                    "role": [
                        "System role protected."
                    ],
                },
            )
        )

        with patch.object(
            APITenantQueryService,
            "get_document",
            return_value={
                "document":
                    self.actor_role,
            },
        ), patch.object(
            RoleManagementService,
            "deactivate_role",
            side_effect=error,
        ):
            response = self.client.post(
                self.role_deactivate_url(
                    self.actor_role
                )
            )

        self.assert_error(
            response,
            422,
        )

    # ==================================================
    # METHODS
    # ==================================================

    def test_role_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.ROLES_URL
        )

        self.assert_error(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )