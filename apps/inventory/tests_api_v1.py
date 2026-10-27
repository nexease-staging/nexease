import json

from datetime import datetime
from decimal import Decimal
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
from apps.core.services.api_query_pipeline_service import (
    APIQueryPipelineError,
    APIQueryPipelineService,
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
from apps.inventory.api.v1.serializers import (
    InventoryAPISerializer,
    StockMovementAPISerializer,
    StockTransferAPISerializer,
    WarehouseAPISerializer,
)
from apps.inventory.repositories.stock_transfer_repository import (
    StockTransferRepository,
)
from apps.inventory.services.stock_transfer_api_service import (
    StockTransferAPIService,
    StockTransferAPIValidationError,
)
from apps.inventory.services.stock_transfer_service import (
    StockTransferService,
)
from apps.inventory.repositories.stock_movement_repository import (
    StockMovementRepository,
)
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)
from apps.inventory.services.inventory_api_service import (
    InventoryAPIService,
    InventoryAPIValidationError,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.inventory.services.warehouse_api_service import (
    WarehouseAPIService,
    WarehouseAPIValidationError,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.inventory.services.inventory_service import (
    InventoryService,
)
from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)

class WarehouseAPIV1RegressionTestCase(
    SimpleTestCase
):

    WAREHOUSES_URL = (
        "/api/v1/warehouses/"
    )
    INVENTORY_URL = (
        "/api/v1/inventory/"
    )
    STOCK_MOVEMENTS_URL = (
        "/api/v1/stock-movements/"
    )
    STOCK_TRANSFERS_URL = (
        "/api/v1/stock-transfers/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Warehouse Test Organization",
            email="warehouse@example.com",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.other_organization = (
            SimpleNamespace(
                id=ObjectId(),
                name="Other Organization",
                email="other@example.com",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
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

        self.warehouse = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            name="Main Warehouse",
            code="MAIN-001",
            address="Warehouse Road",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            pincode="400001",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.product = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            sku="PHONE-001",
            name="Smart Phone",
            unit="piece",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.inventory = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("100.00"),
            reserved_quantity=Decimal("20.00"),
            created_at=now,
            updated_at=now,
        )

        self.stock_movement = (
            SimpleNamespace(
                id=ObjectId(),
                organization=self.organization,
                inventory=self.inventory,
                product=self.product,
                warehouse=self.warehouse,
                movement_type="ADJUSTMENT_OUT",
                quantity=Decimal("-5.00"),
                quantity_before=Decimal("100.00"),
                quantity_after=Decimal("95.00"),
                reserved_before=Decimal("20.00"),
                reserved_after=Decimal("20.00"),
                reference_type="PHYSICAL_COUNT",
                reference_id="COUNT-001",
                notes="Physical count correction",
                created_by=self.user,
                created_at=now,
            )
        )

        self.destination_warehouse = (
            SimpleNamespace(
                id=ObjectId(),
                organization=self.organization,
                name="Secondary Warehouse",
                code="SECONDARY-001",
                address="Secondary Road",
                city="Pune",
                state="Maharashtra",
                country="India",
                pincode="411001",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )

        self.destination_inventory = (
            SimpleNamespace(
                id=ObjectId(),
                organization=self.organization,
                product=self.product,
                warehouse=(
                    self.destination_warehouse
                ),
                quantity=Decimal("10.00"),
                reserved_quantity=Decimal("0.00"),
                created_at=now,
                updated_at=now,
            )
        )

        self.stock_transfer = (
            SimpleNamespace(
                id=ObjectId(),
                organization=self.organization,
                transfer_number="TRF-TEST001",
                product=self.product,
                source_warehouse=self.warehouse,
                destination_warehouse=(
                    self.destination_warehouse
                ),
                source_inventory=self.inventory,
                destination_inventory=(
                    self.destination_inventory
                ),
                quantity=Decimal("5.00"),
                status="COMPLETED",
                notes="Test transfer",
                created_by=self.user,
                created_at=now,
                completed_at=now,
            )
        )

        self.organization_context = {
            "user":
                self.user,
            "organization":
                self.organization,
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

    def detail_url(self):
        return (
            f"{self.WAREHOUSES_URL}"
            f"{self.warehouse.id}/"
        )

    def activate_url(self):
        return (
            f"{self.WAREHOUSES_URL}"
            f"{self.warehouse.id}/activate/"
        )

    def deactivate_url(self):
        return (
            f"{self.WAREHOUSES_URL}"
            f"{self.warehouse.id}/deactivate/"
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
            body.get(
                "request_id"
            )
        )

        return body

    # ==================================================
    # AUTHENTICATION
    # ==================================================

    def test_anonymous_warehouse_list_is_rejected(
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
                self.WAREHOUSES_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    # ==================================================
    # LIST
    # ==================================================

    def test_warehouse_list_uses_query_pipeline(
        self,
    ):
        queryset_marker = object()

        pipeline_result = {
            "items": [
                self.warehouse,
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": "main",
                "filters": {
                    "is_active": True,
                },
                "sort": [
                    "name",
                ],
            },
        }

        with (
            patch.object(
                WarehouseRepository,
                "queryset_for_organization",
                return_value=queryset_marker,
            ) as queryset_mock,
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ) as pipeline_mock,
        ):
            response = self.client.get(
                (
                    f"{self.WAREHOUSES_URL}"
                    "?search=main"
                    "&is_active=true"
                    "&sort=name"
                )
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            len(
                body["data"]["warehouses"]
            ),
            1,
        )

        self.assertEqual(
            body["data"]["warehouses"][0][
                "code"
            ],
            "MAIN-001",
        )

        queryset_mock.assert_called_once_with(
            organization=self.organization,
        )

        pipeline_mock.assert_called_once()

    def test_warehouse_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.WAREHOUSES_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # CREATE
    # ==================================================

    def test_create_warehouse_returns_201(
        self,
    ):
        payload = {
            "name": "Main Warehouse",
            "code": "main-001",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
        }

        with patch.object(
            WarehouseAPIService,
            "create_warehouse",
            return_value=self.warehouse,
        ) as create_mock:
            response = self.client.post(
                self.WAREHOUSES_URL,
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        self.assertEqual(
            body["data"]["warehouse"]["code"],
            "MAIN-001",
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            payload=payload,
        )

    def test_create_warehouse_validation_error_uses_contract(
        self,
    ):
        validation_error = (
            WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details={
                    "code": [
                        (
                            "A warehouse with this "
                            "code already exists."
                        )
                    ],
                },
            )
        )

        with patch.object(
            WarehouseAPIService,
            "create_warehouse",
            side_effect=validation_error,
        ):
            response = self.client.post(
                self.WAREHOUSES_URL,
                data=json.dumps({
                    "name": "Main Warehouse",
                    "code": "MAIN-001",
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "code",
            body["error"]["details"],
        )

    def test_create_warehouse_requires_json_content_type(
        self,
    ):
        response = self.client.post(
            self.WAREHOUSES_URL,
            data="name=Main Warehouse",
            content_type=(
                "application/x-www-form-urlencoded"
            ),
        )

        self.assert_error_contract(
            response,
            400,
            "BAD_REQUEST",
        )

    # ==================================================
    # DETAIL
    # ==================================================

    def test_warehouse_detail_returns_warehouse(
        self,
    ):
        with patch.object(
            WarehouseAPIService,
            "get_warehouse",
            return_value=self.warehouse,
        ) as get_mock:
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["warehouse"]["id"],
            str(
                self.warehouse.id
            ),
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            warehouse_id=str(
                self.warehouse.id
            ),
        )

    def test_missing_warehouse_returns_not_found(
        self,
    ):
        with patch.object(
            WarehouseAPIService,
            "get_warehouse",
            side_effect=LookupError(
                "Warehouse not found."
            ),
        ):
            response = self.client.get(
                self.detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    # ==================================================
    # UPDATE
    # ==================================================

    def test_update_warehouse_returns_updated_warehouse(
        self,
    ):
        payload = {
            "name":
                "Updated Warehouse",
            "city":
                "Pune",
        }

        updated_warehouse = (
            SimpleNamespace(
                **{
                    **vars(
                        self.warehouse
                    ),
                    "name":
                        "Updated Warehouse",
                    "city":
                        "Pune",
                }
            )
        )

        with patch.object(
            WarehouseAPIService,
            "update_warehouse",
            return_value=updated_warehouse,
        ) as update_mock:
            response = self.client.patch(
                self.detail_url(),
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["warehouse"]["name"],
            "Updated Warehouse",
        )

        update_mock.assert_called_once_with(
            organization=self.organization,
            warehouse_id=str(
                self.warehouse.id
            ),
            payload=payload,
        )

    # ==================================================
    # LIFECYCLE
    # ==================================================

    def test_activate_warehouse(
        self,
    ):
        activated = SimpleNamespace(
            **{
                **vars(
                    self.warehouse
                ),
                "is_active": True,
            }
        )

        with patch.object(
            WarehouseAPIService,
            "activate_warehouse",
            return_value=activated,
        ):
            response = self.client.post(
                self.activate_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertTrue(
            body["data"]["warehouse"][
                "is_active"
            ]
        )

    def test_deactivate_warehouse(
        self,
    ):
        deactivated = SimpleNamespace(
            **{
                **vars(
                    self.warehouse
                ),
                "is_active": False,
            }
        )

        with patch.object(
            WarehouseAPIService,
            "deactivate_warehouse",
            return_value=deactivated,
        ):
            response = self.client.post(
                self.deactivate_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertFalse(
            body["data"]["warehouse"][
                "is_active"
            ]
        )

    # ==================================================
    # METHOD RESTRICTIONS
    # ==================================================

    def test_warehouse_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.WAREHOUSES_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_warehouse_detail_rejects_put(
        self,
    ):
        response = self.client.put(
            self.detail_url(),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # QUERY PIPELINE ERROR
    # ==================================================

    def test_warehouse_query_error_uses_contract(
        self,
    ):
        pipeline_error = (
            APIQueryPipelineError(
                component="sorting",
                message=(
                    "Unsupported sorting field."
                ),
                details={
                    "sort": [
                        (
                            "The requested sorting "
                            "field is not supported."
                        )
                    ],
                },
            )
        )

        with (
            patch.object(
                WarehouseRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                side_effect=pipeline_error,
            ),
        ):
            response = self.client.get(
                (
                    f"{self.WAREHOUSES_URL}"
                    "?sort=$where"
                )
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertEqual(
            body["error"]["details"][
                "component"
            ],
            "sorting",
        )

        self.assertIn(
            "sort",
            body["error"]["details"][
                "fields"
            ],
        )

    # ==================================================
    # SERIALIZER SAFETY
    # ==================================================

    def test_warehouse_serializer_has_safe_fields(
        self,
    ):
        serialized = (
            WarehouseAPISerializer
            .serialize_detail(
                self.warehouse
            )
        )

        self.assertEqual(
            serialized["id"],
            str(
                self.warehouse.id
            ),
        )

        self.assertEqual(
            serialized["code"],
            "MAIN-001",
        )

        self.assertNotIn(
            "organization",
            serialized,
        )

        self.assertNotIn(
            "_data",
            serialized,
        )

        self.assertNotIn(
            "_cls",
            serialized,
        )

    # ==================================================
    # SERVICE VALIDATION
    # ==================================================

    def test_service_normalizes_create_payload(
        self,
    ):
        payload = {
            "name":
                " Main Warehouse ",
            "code":
                " main-002 ",
            "address":
                " Warehouse Road ",
            "city":
                " Mumbai ",
            "state":
                " Maharashtra ",
            "country":
                " India ",
            "pincode":
                " 400001 ",
        }

        with (
            patch.object(
                WarehouseRepository,
                "code_exists",
                return_value=False,
            ),
            patch.object(
                WarehouseRepository,
                "name_exists",
                return_value=False,
            ),
        ):
            values = (
                WarehouseAPIService
                .validate_create_payload(
                    organization=(
                        self.organization
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            values["name"],
            "Main Warehouse",
        )

        self.assertEqual(
            values["code"],
            "MAIN-002",
        )

        self.assertEqual(
            values["city"],
            "Mumbai",
        )

        self.assertEqual(
            values["pincode"],
            "400001",
        )

    def test_service_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            WarehouseAPIValidationError
        ) as context:
            (
                WarehouseAPIService
                .validate_update_payload(
                    organization=(
                        self.organization
                    ),
                    warehouse=(
                        self.warehouse
                    ),
                    payload={
                        "organization_id":
                            str(
                                self.other_organization.id
                            ),
                        "is_active":
                            False,
                    },
                )
            )

        self.assertIn(
            "organization_id",
            context.exception.details,
        )

        self.assertIn(
            "is_active",
            context.exception.details,
        )

    def test_service_rejects_empty_update(
        self,
    ):
        with self.assertRaises(
            WarehouseAPIValidationError
        ) as context:
            (
                WarehouseAPIService
                .validate_update_payload(
                    organization=(
                        self.organization
                    ),
                    warehouse=(
                        self.warehouse
                    ),
                    payload={},
                )
            )

        self.assertIn(
            "body",
            context.exception.details,
        )

    def test_service_treats_malformed_id_as_missing(
        self,
    ):
        with patch.object(
            WarehouseRepository,
            "get_by_id",
            return_value=None,
        ) as get_mock:
            with self.assertRaises(
                LookupError
            ):
                (
                    WarehouseAPIService
                    .get_warehouse(
                        organization=(
                            self.organization
                        ),
                        warehouse_id=(
                            "not-an-object-id"
                        ),
                    )
                )

        get_mock.assert_called_once_with(
            organization=self.organization,
            warehouse_id="not-an-object-id",
        )

    # ==================================================
    # PERMISSION AND LIFECYCLE ERRORS
    # ==================================================

    def test_create_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.WAREHOUSES_URL,
                data=json.dumps({
                    "name": "New Warehouse",
                    "code": "NEW-001",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_activate_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.activate_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_deactivate_missing_warehouse_returns_not_found(
        self,
    ):
        with patch.object(
            WarehouseAPIService,
            "deactivate_warehouse",
            side_effect=LookupError(
                "Warehouse not found."
            ),
        ):
            response = self.client.post(
                self.deactivate_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def inventory_detail_url(self):
        return (
            f"{self.INVENTORY_URL}"
            f"{self.inventory.id}/"
        )

    # ==================================================
    # INVENTORY AUTHENTICATION
    # ==================================================

    def test_anonymous_inventory_list_is_rejected(
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
                self.INVENTORY_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    # ==================================================
    # INVENTORY LIST
    # ==================================================

    def test_inventory_list_uses_query_pipeline(
        self,
    ):
        queryset_marker = object()

        pipeline_result = {
            "items": [
                self.inventory,
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": None,
                "filters": {
                    "warehouse_id": str(
                        self.warehouse.id
                    ),
                },
                "sort": [
                    "-updated_at",
                ],
            },
        }

        with (
            patch.object(
                InventoryRepository,
                "queryset_for_organization",
                return_value=queryset_marker,
            ) as queryset_mock,
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ) as pipeline_mock,
        ):
            response = self.client.get(
                (
                    f"{self.INVENTORY_URL}"
                    f"?warehouse_id="
                    f"{self.warehouse.id}"
                    "&sort=-updated_at"
                )
            )

        body = self.assert_success_contract(
            response
        )

        inventory_items = (
            body["data"]["inventory"]
        )

        self.assertEqual(
            len(
                inventory_items
            ),
            1,
        )

        self.assertEqual(
            inventory_items[0][
                "available_quantity"
            ],
            "80.00",
        )

        queryset_mock.assert_called_once_with(
            organization=self.organization,
        )

        pipeline_mock.assert_called_once()

    def test_inventory_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.INVENTORY_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_inventory_list_rejects_invalid_reference_filter(
        self,
    ):
        with patch.object(
            InventoryRepository,
            "queryset_for_organization",
            return_value=object(),
        ):
            response = self.client.get(
                (
                    f"{self.INVENTORY_URL}"
                    "?warehouse_id=invalid-id"
                )
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertEqual(
            body["error"]["details"][
                "component"
            ],
            "filtering",
        )

        self.assertIn(
            "warehouse_id",
            body["error"]["details"][
                "fields"
            ],
        )

    # ==================================================
    # INVENTORY CREATE
    # ==================================================

    def test_create_inventory_returns_201(
        self,
    ):
        payload = {
            "product_id":
                str(
                    self.product.id
                ),
            "warehouse_id":
                str(
                    self.warehouse.id
                ),
            "quantity":
                "100.00",
        }

        with patch.object(
            InventoryAPIService,
            "create_inventory",
            return_value=self.inventory,
        ) as create_mock:
            response = self.client.post(
                self.INVENTORY_URL,
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        self.assertEqual(
            body["data"]["inventory"][
                "quantity"
            ],
            "100.00",
        )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            payload=payload,
        )

    def test_create_inventory_validation_error_uses_contract(
        self,
    ):
        validation_error = (
            InventoryAPIValidationError(
                "Inventory validation failed.",
                details={
                    "inventory": [
                        (
                            "Inventory already "
                            "exists."
                        )
                    ],
                },
            )
        )

        with patch.object(
            InventoryAPIService,
            "create_inventory",
            side_effect=validation_error,
        ):
            response = self.client.post(
                self.INVENTORY_URL,
                data=json.dumps({
                    "product_id":
                        str(
                            self.product.id
                        ),
                    "warehouse_id":
                        str(
                            self.warehouse.id
                        ),
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "inventory",
            body["error"]["details"],
        )

    def test_create_inventory_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.INVENTORY_URL,
                data=json.dumps({
                    "product_id":
                        str(
                            self.product.id
                        ),
                    "warehouse_id":
                        str(
                            self.warehouse.id
                        ),
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # INVENTORY DETAIL
    # ==================================================

    def test_inventory_detail_returns_balance(
        self,
    ):
        with patch.object(
            InventoryAPIService,
            "get_inventory",
            return_value=self.inventory,
        ) as get_mock:
            response = self.client.get(
                self.inventory_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        inventory = (
            body["data"]["inventory"]
        )

        self.assertEqual(
            inventory["id"],
            str(
                self.inventory.id
            ),
        )

        self.assertEqual(
            inventory[
                "available_quantity"
            ],
            "80.00",
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            inventory_id=str(
                self.inventory.id
            ),
        )

    def test_missing_inventory_returns_not_found(
        self,
    ):
        with patch.object(
            InventoryAPIService,
            "get_inventory",
            side_effect=LookupError(
                "Inventory not found."
            ),
        ):
            response = self.client.get(
                self.inventory_detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    # ==================================================
    # INVENTORY SERIALIZER
    # ==================================================

    def test_inventory_serializer_is_tenant_safe(
        self,
    ):
        serialized = (
            InventoryAPISerializer
            .serialize_detail(
                self.inventory
            )
        )

        self.assertEqual(
            serialized["product"]["id"],
            str(
                self.product.id
            ),
        )

        self.assertEqual(
            serialized["warehouse"]["id"],
            str(
                self.warehouse.id
            ),
        )

        self.assertEqual(
            serialized[
                "available_quantity"
            ],
            "80.00",
        )

        self.assertNotIn(
            "organization",
            serialized,
        )

        self.assertNotIn(
            "_data",
            serialized,
        )

    # ==================================================
    # INVENTORY SERVICE VALIDATION
    # ==================================================

    def test_inventory_service_normalizes_create_payload(
        self,
    ):
        payload = {
            "product_id":
                f" {self.product.id} ",
            "warehouse_id":
                f" {self.warehouse.id} ",
            "quantity":
                "25.50",
        }

        with (
            patch.object(
                ProductRepository,
                "get_by_id",
                return_value=self.product,
            ),
            patch.object(
                WarehouseRepository,
                "get_by_id",
                return_value=self.warehouse,
            ),
            patch.object(
                InventoryRepository,
                (
                    "exists_for_product_"
                    "and_warehouse"
                ),
                return_value=False,
            ),
        ):
            values = (
                InventoryAPIService
                .validate_create_payload(
                    organization=(
                        self.organization
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            values["product"],
            self.product,
        )

        self.assertEqual(
            values["warehouse"],
            self.warehouse,
        )

        self.assertEqual(
            values["quantity"],
            Decimal("25.50"),
        )

    def test_inventory_service_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            InventoryAPIValidationError
        ) as context:
            (
                InventoryAPIService
                .validate_create_payload(
                    organization=(
                        self.organization
                    ),
                    payload={
                        "organization_id":
                            str(
                                self.other_organization.id
                            ),
                        "reserved_quantity":
                            "10.00",
                    },
                )
            )

        self.assertIn(
            "organization_id",
            context.exception.details,
        )

        self.assertIn(
            "reserved_quantity",
            context.exception.details,
        )

    # ==================================================
    # INVENTORY METHOD RESTRICTIONS
    # ==================================================

    def test_inventory_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.INVENTORY_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_inventory_detail_rejects_patch(
        self,
    ):
        response = self.client.patch(
            self.inventory_detail_url(),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def inventory_adjust_url(self):
        return (
            f"{self.INVENTORY_URL}"
            f"{self.inventory.id}/adjust/"
        )

    # ==================================================
    # INVENTORY ADJUSTMENT API
    # ==================================================

    def test_adjust_inventory_returns_updated_balance(
        self,
    ):
        payload = {
            "quantity_change":
                "-5.00",
            "reference_type":
                "PHYSICAL_COUNT",
            "reference_id":
                "COUNT-001",
            "notes":
                "Physical count adjustment",
        }

        adjusted_inventory = (
            SimpleNamespace(
                **{
                    **vars(
                        self.inventory
                    ),
                    "quantity":
                        Decimal("95.00"),
                }
            )
        )

        with patch.object(
            InventoryAPIService,
            "adjust_inventory",
            return_value=adjusted_inventory,
        ) as adjust_mock:
            response = self.client.post(
                self.inventory_adjust_url(),
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["inventory"][
                "quantity"
            ],
            "95.00",
        )

        self.assertEqual(
            body["data"]["inventory"][
                "available_quantity"
            ],
            "75.00",
        )

        adjust_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            inventory_id=str(
                self.inventory.id
            ),
            payload=payload,
        )

    def test_adjust_inventory_validation_error_uses_contract(
        self,
    ):
        validation_error = (
            InventoryAPIValidationError(
                (
                    "Inventory adjustment "
                    "validation failed."
                ),
                details={
                    "quantity_change": [
                        (
                            "Quantity change cannot "
                            "be zero."
                        )
                    ],
                },
            )
        )

        with patch.object(
            InventoryAPIService,
            "adjust_inventory",
            side_effect=validation_error,
        ):
            response = self.client.post(
                self.inventory_adjust_url(),
                data=json.dumps({
                    "quantity_change": "0",
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "quantity_change",
            body["error"]["details"],
        )

    def test_adjust_missing_inventory_returns_not_found(
        self,
    ):
        with patch.object(
            InventoryAPIService,
            "adjust_inventory",
            side_effect=LookupError(
                "Inventory not found."
            ),
        ):
            response = self.client.post(
                self.inventory_adjust_url(),
                data=json.dumps({
                    "quantity_change": "5.00",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_adjust_inventory_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.inventory_adjust_url(),
                data=json.dumps({
                    "quantity_change": "5.00",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_adjust_inventory_rejects_get(
        self,
    ):
        response = self.client.get(
            self.inventory_adjust_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # ADJUSTMENT VALIDATION
    # ==================================================

    def test_adjustment_service_normalizes_payload(
        self,
    ):
        values = (
            InventoryAPIService
            .validate_adjustment_payload(
                payload={
                    "quantity_change":
                        " 5.50 ",
                    "reference_type":
                        " PHYSICAL_COUNT ",
                    "reference_id":
                        " COUNT-001 ",
                    "notes":
                        " Count correction ",
                }
            )
        )

        self.assertEqual(
            values["quantity_change"],
            Decimal("5.50"),
        )

        self.assertEqual(
            values["reference_type"],
            "PHYSICAL_COUNT",
        )

        self.assertEqual(
            values["reference_id"],
            "COUNT-001",
        )

        self.assertEqual(
            values["notes"],
            "Count correction",
        )

    def test_adjustment_service_rejects_zero(
        self,
    ):
        with self.assertRaises(
            InventoryAPIValidationError
        ) as context:
            (
                InventoryAPIService
                .validate_adjustment_payload(
                    payload={
                        "quantity_change": "0",
                    }
                )
            )

        self.assertIn(
            "quantity_change",
            context.exception.details,
        )

    def test_adjustment_service_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            InventoryAPIValidationError
        ) as context:
            (
                InventoryAPIService
                .validate_adjustment_payload(
                    payload={
                        "quantity_change":
                            "5.00",
                        "warehouse_id":
                            str(
                                self.warehouse.id
                            ),
                        "quantity":
                            "999.00",
                    }
                )
            )

        self.assertIn(
            "warehouse_id",
            context.exception.details,
        )

        self.assertIn(
            "quantity",
            context.exception.details,
        )

    def test_adjustment_service_delegates_to_inventory_service(
        self,
    ):
        payload = {
            "quantity_change": "-5.00",
        }

        with (
            patch.object(
                InventoryAPIService,
                "get_inventory",
                return_value=self.inventory,
            ),
            patch.object(
                InventoryService,
                "adjust_quantity",
                return_value=self.inventory,
            ) as service_mock,
        ):
            result = (
                InventoryAPIService
                .adjust_inventory(
                    user=self.user,
                    organization=(
                        self.organization
                    ),
                    inventory_id=str(
                        self.inventory.id
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            result,
            self.inventory,
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            inventory_id=str(
                self.inventory.id
            ),
            quantity_change=Decimal("-5.00"),
            reference_type="",
            reference_id="",
            notes="",
        )

    # ==================================================
    # ADJUSTMENT ROLLBACK
    # ==================================================

    def test_adjustment_rolls_back_when_ledger_write_fails(
        self,
    ):
        saved_quantities = []

        def update_quantity(
            *,
            inventory,
            quantity,
        ):
            saved_quantities.append(
                quantity
            )

            inventory.quantity = quantity

            return inventory

        with (
            patch.object(
                InventoryRepository,
                "get_by_id",
                return_value=self.inventory,
            ),
            patch.object(
                InventoryRepository,
                "update_quantity",
                side_effect=update_quantity,
            ),
            patch.object(
                StockMovementService,
                "create_movement",
                side_effect=RuntimeError(
                    "Ledger write failed."
                ),
            ),
        ):
            with self.assertRaises(
                RuntimeError
            ):
                (
                    InventoryService
                    .adjust_quantity(
                        user=self.user,
                        organization=(
                            self.organization
                        ),
                        inventory_id=str(
                            self.inventory.id
                        ),
                        quantity_change=(
                            Decimal("-5.00")
                        ),
                    )
                )

        self.assertEqual(
            saved_quantities,
            [
                Decimal("95.00"),
                Decimal("100.00"),
            ],
        )

        self.assertEqual(
            self.inventory.quantity,
            Decimal("100.00"),
        )

    def stock_movement_detail_url(self):
        return (
            f"{self.STOCK_MOVEMENTS_URL}"
            f"{self.stock_movement.id}/"
        )

    # ==================================================
    # STOCK MOVEMENT AUTHENTICATION
    # ==================================================

    def test_anonymous_stock_movement_list_is_rejected(
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
                self.STOCK_MOVEMENTS_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    # ==================================================
    # STOCK MOVEMENT LIST
    # ==================================================

    def test_stock_movement_list_uses_query_pipeline(
        self,
    ):
        queryset_marker = object()

        pipeline_result = {
            "items": [
                self.stock_movement,
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": None,
                "filters": {
                    "movement_type":
                        "ADJUSTMENT_OUT",
                },
                "sort": [
                    "-created_at",
                ],
            },
        }

        with (
            patch.object(
                StockMovementRepository,
                "queryset_for_organization",
                return_value=queryset_marker,
            ) as queryset_mock,
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ) as pipeline_mock,
        ):
            response = self.client.get(
                (
                    f"{self.STOCK_MOVEMENTS_URL}"
                    "?movement_type=ADJUSTMENT_OUT"
                )
            )

        body = self.assert_success_contract(
            response
        )

        movements = (
            body["data"]["movements"]
        )

        self.assertEqual(
            len(
                movements
            ),
            1,
        )

        self.assertEqual(
            movements[0]["movement_type"],
            "ADJUSTMENT_OUT",
        )

        self.assertEqual(
            movements[0]["quantity"],
            "-5.00",
        )

        queryset_mock.assert_called_once_with(
            organization=self.organization,
        )

        pipeline_mock.assert_called_once()

    def test_stock_movement_list_rejects_invalid_type(
        self,
    ):
        with patch.object(
            StockMovementRepository,
            "queryset_for_organization",
            return_value=object(),
        ):
            response = self.client.get(
                (
                    f"{self.STOCK_MOVEMENTS_URL}"
                    "?movement_type=INVALID_TYPE"
                )
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertEqual(
            body["error"]["details"][
                "component"
            ],
            "filtering",
        )

        self.assertIn(
            "movement_type",
            body["error"]["details"][
                "fields"
            ],
        )

    def test_stock_movement_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.STOCK_MOVEMENTS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # STOCK MOVEMENT DETAIL
    # ==================================================

    def test_stock_movement_detail_returns_movement(
        self,
    ):
        with patch.object(
            StockMovementService,
            "get_movement",
            return_value=self.stock_movement,
        ) as get_mock:
            response = self.client.get(
                self.stock_movement_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        movement = (
            body["data"]["movement"]
        )

        self.assertEqual(
            movement["id"],
            str(
                self.stock_movement.id
            ),
        )

        self.assertEqual(
            movement["reference"]["id"],
            "COUNT-001",
        )

        get_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            movement_id=str(
                self.stock_movement.id
            ),
        )

    def test_missing_stock_movement_returns_not_found(
        self,
    ):
        with patch.object(
            StockMovementService,
            "get_movement",
            side_effect=ValueError(
                "Stock movement not found."
            ),
        ):
            response = self.client.get(
                self.stock_movement_detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    # ==================================================
    # STOCK MOVEMENT SERIALIZER
    # ==================================================

    def test_stock_movement_serializer_is_safe(
        self,
    ):
        serialized = (
            StockMovementAPISerializer
            .serialize_detail(
                self.stock_movement
            )
        )

        self.assertEqual(
            serialized["inventory_id"],
            str(
                self.inventory.id
            ),
        )

        self.assertEqual(
            serialized["product"]["sku"],
            "PHONE-001",
        )

        self.assertEqual(
            serialized["warehouse"]["code"],
            "MAIN-001",
        )

        self.assertNotIn(
            "organization",
            serialized,
        )

        self.assertNotIn(
            "_data",
            serialized,
        )

    # ==================================================
    # STOCK MOVEMENT IMMUTABILITY
    # ==================================================

    def test_stock_movement_collection_rejects_post(
        self,
    ):
        response = self.client.post(
            self.STOCK_MOVEMENTS_URL,
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_stock_movement_detail_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.stock_movement_detail_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def stock_transfer_detail_url(self):
        return (
            f"{self.STOCK_TRANSFERS_URL}"
            f"{self.stock_transfer.id}/"
        )

    

    # ==================================================
    # STOCK TRANSFER LIST
    # ==================================================

    def test_stock_transfer_list_uses_query_pipeline(
        self,
    ):
        pipeline_result = {
            "items": [
                self.stock_transfer,
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": None,
                "filters": {
                    "status": "COMPLETED",
                },
                "sort": [
                    "-created_at",
                ],
            },
        }

        with (
            patch.object(
                StockTransferRepository,
                "queryset_for_organization",
                return_value=object(),
            ) as queryset_mock,
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ) as pipeline_mock,
        ):
            response = self.client.get(
                (
                    f"{self.STOCK_TRANSFERS_URL}"
                    "?status=COMPLETED"
                )
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            len(
                body["data"]["transfers"]
            ),
            1,
        )

        self.assertEqual(
            body["data"]["transfers"][0][
                "transfer_number"
            ],
            "TRF-TEST001",
        )

        queryset_mock.assert_called_once_with(
            organization=self.organization,
        )

        pipeline_mock.assert_called_once()

    def test_stock_transfer_list_rejects_invalid_status(
        self,
    ):
        with patch.object(
            StockTransferRepository,
            "queryset_for_organization",
            return_value=object(),
        ):
            response = self.client.get(
                (
                    f"{self.STOCK_TRANSFERS_URL}"
                    "?status=INVALID"
                )
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertEqual(
            body["error"]["details"][
                "component"
            ],
            "filtering",
        )

    # ==================================================
    # STOCK TRANSFER CREATE
    # ==================================================

    def test_create_stock_transfer_returns_201(
        self,
    ):
        payload = {
            "product_id":
                str(
                    self.product.id
                ),
            "source_warehouse_id":
                str(
                    self.warehouse.id
                ),
            "destination_warehouse_id":
                str(
                    self.destination_warehouse.id
                ),
            "quantity":
                "5.00",
            "notes":
                "Test transfer",
        }

        with patch.object(
            StockTransferAPIService,
            "create_transfer",
            return_value=self.stock_transfer,
        ) as create_mock:
            response = self.client.post(
                self.STOCK_TRANSFERS_URL,
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        self.assertEqual(
            body["data"]["transfer"][
                "status"
            ],
            "COMPLETED",
        )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            payload=payload,
        )

    def test_create_stock_transfer_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.STOCK_TRANSFERS_URL,
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # STOCK TRANSFER DETAIL
    # ==================================================

    def test_stock_transfer_detail_returns_transfer(
        self,
    ):
        with patch.object(
            StockTransferAPIService,
            "get_transfer",
            return_value=self.stock_transfer,
        ) as get_mock:
            response = self.client.get(
                self.stock_transfer_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        transfer = (
            body["data"]["transfer"]
        )

        self.assertEqual(
            transfer["id"],
            str(
                self.stock_transfer.id
            ),
        )

        self.assertEqual(
            transfer["source_inventory_id"],
            str(
                self.inventory.id
            ),
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            transfer_id=str(
                self.stock_transfer.id
            ),
        )

    def test_missing_stock_transfer_returns_not_found(
        self,
    ):
        with patch.object(
            StockTransferAPIService,
            "get_transfer",
            side_effect=LookupError(
                "Stock transfer not found."
            ),
        ):
            response = self.client.get(
                self.stock_transfer_detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    # ==================================================
    # TRANSFER SERIALIZER
    # ==================================================

    def test_stock_transfer_serializer_is_safe(
        self,
    ):
        serialized = (
            StockTransferAPISerializer
            .serialize_detail(
                self.stock_transfer
            )
        )

        self.assertEqual(
            serialized["product"]["sku"],
            "PHONE-001",
        )

        self.assertEqual(
            serialized[
                "source_warehouse"
            ]["code"],
            "MAIN-001",
        )

        self.assertEqual(
            serialized[
                "destination_warehouse"
            ]["code"],
            "SECONDARY-001",
        )

        self.assertNotIn(
            "organization",
            serialized,
        )

        self.assertNotIn(
            "_data",
            serialized,
        )

    # ==================================================
    # TRANSFER VALIDATION
    # ==================================================

    def test_transfer_service_normalizes_payload(
        self,
    ):
        payload = {
            "product_id":
                f" {self.product.id} ",
            "source_warehouse_id":
                f" {self.warehouse.id} ",
            "destination_warehouse_id":
                (
                    f" "
                    f"{self.destination_warehouse.id}"
                    f" "
                ),
            "quantity":
                "5.50",
            "notes":
                " Transfer stock ",
        }

        with (
            patch.object(
                ProductRepository,
                "get_by_id",
                return_value=self.product,
            ),
            patch.object(
                WarehouseRepository,
                "get_by_id",
                side_effect=[
                    self.warehouse,
                    self.destination_warehouse,
                ],
            ),
        ):
            values = (
                StockTransferAPIService
                .validate_transfer_payload(
                    organization=(
                        self.organization
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            values["quantity"],
            Decimal("5.50"),
        )

        self.assertEqual(
            values["notes"],
            "Transfer stock",
        )

        self.assertEqual(
            values["source_warehouse"],
            self.warehouse,
        )

    def test_transfer_service_rejects_same_warehouse(
        self,
    ):
        payload = {
            "product_id":
                str(
                    self.product.id
                ),
            "source_warehouse_id":
                str(
                    self.warehouse.id
                ),
            "destination_warehouse_id":
                str(
                    self.warehouse.id
                ),
            "quantity":
                "5.00",
        }

        with (
            patch.object(
                ProductRepository,
                "get_by_id",
                return_value=self.product,
            ),
            patch.object(
                WarehouseRepository,
                "get_by_id",
                return_value=self.warehouse,
            ),
        ):
            with self.assertRaises(
                StockTransferAPIValidationError
            ) as context:
                (
                    StockTransferAPIService
                    .validate_transfer_payload(
                        organization=(
                            self.organization
                        ),
                        payload=payload,
                    )
                )

        self.assertIn(
            "destination_warehouse_id",
            context.exception.details,
        )

    # ==================================================
    # TRANSFER ROLLBACK
    # ==================================================

    def test_transfer_rolls_back_when_second_movement_fails(
        self,
    ):
        saved_quantities = []

        def update_quantity(
            *,
            inventory,
            quantity,
        ):
            saved_quantities.append(
                quantity
            )

            inventory.quantity = quantity

            return inventory

        transfer_out = SimpleNamespace(
            id=ObjectId()
        )

        with (
            patch.object(
                InventoryRepository,
                "get_by_product_and_warehouse",
                side_effect=[
                    self.inventory,
                    self.destination_inventory,
                ],
            ),
            patch.object(
                InventoryRepository,
                "update_quantity",
                side_effect=update_quantity,
            ),
            patch.object(
                StockTransferRepository,
                "create_transfer",
                return_value=self.stock_transfer,
            ),
            patch.object(
                StockMovementService,
                "create_movement",
                side_effect=[
                    transfer_out,
                    RuntimeError(
                        "Second movement failed."
                    ),
                ],
            ),
            patch.object(
                StockMovementRepository,
                "delete_movement",
                return_value=True,
            ) as delete_movement_mock,
            patch.object(
                StockTransferRepository,
                "delete_transfer",
                return_value=True,
            ) as delete_transfer_mock,
        ):
            with self.assertRaises(
                RuntimeError
            ):
                (
                    StockTransferService
                    .transfer_stock(
                        user=self.user,
                        organization=(
                            self.organization
                        ),
                        product=self.product,
                        source_warehouse=(
                            self.warehouse
                        ),
                        destination_warehouse=(
                            self.destination_warehouse
                        ),
                        quantity=Decimal("5.00"),
                        notes="Test rollback",
                    )
                )

        self.assertEqual(
            self.inventory.quantity,
            Decimal("100.00"),
        )

        self.assertEqual(
            self.destination_inventory.quantity,
            Decimal("10.00"),
        )

        self.assertEqual(
            saved_quantities,
            [
                Decimal("95.00"),
                Decimal("15.00"),
                Decimal("100.00"),
                Decimal("10.00"),
            ],
        )

        self.assertEqual(
            delete_movement_mock.call_count,
            2,
        )

        delete_transfer_mock.assert_called_once_with(
            transfer=self.stock_transfer,
        )

    # ==================================================
    # TRANSFER METHOD RESTRICTIONS
    # ==================================================

    def test_stock_transfer_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.STOCK_TRANSFERS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_stock_transfer_detail_rejects_patch(
        self,
    ):
        response = self.client.patch(
            self.stock_transfer_detail_url(),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )