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
from apps.products.services.category_api_service import (
    CategoryAPIService,
)
from apps.authorization.services import (
    AuthorizationService,
)
from apps.products.models import Category, Product
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
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.products.api.v1.serializers import (
    ProductAPISerializer,
)
from apps.products.repositories.category_repository import (
    CategoryRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.products.services.product_api_service import (
    ProductAPIService,
    ProductAPIValidationError,
)


class ProductAPIV1RegressionTestCase(
    SimpleTestCase
):

    PRODUCTS_URL = (
        "/api/v1/products/"
    )

    CATEGORIES_URL = (
        "/api/v1/categories/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Product Regression Organization",
            email="products@example.com",
            phone="9999999999",
            address="Regression Test Address",
            country="India",
            currency="INR",
            timezone="Asia/Kolkata",
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

        self.category = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            name="Electronics",
            description="Electronic products.",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.product = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            sku="PHONE-001",
            name="Smart Phone",
            description="Regression test product.",
            category=self.category,
            brand="Example Brand",
            unit="piece",
            cost_price=Decimal("10000.00"),
            selling_price=Decimal("15000.00"),
            barcode="890000000001",
            is_active=True,
            created_at=now,
            updated_at=now,
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

    def detail_url(
        self,
        product=None,
    ):
        product = (
            product
            or
            self.product
        )

        return (
            f"{self.PRODUCTS_URL}"
            f"{product.id}/"
        )

    def activate_url(
        self,
        product=None,
    ):
        product = (
            product
            or
            self.product
        )

        return (
            f"{self.PRODUCTS_URL}"
            f"{product.id}/activate/"
        )

    def deactivate_url(
        self,
        product=None,
    ):
        product = (
            product
            or
            self.product
        )

        return (
            f"{self.PRODUCTS_URL}"
            f"{product.id}/deactivate/"
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

    def test_anonymous_product_list_is_rejected(
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
                self.PRODUCTS_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    # ==================================================
    # CATEGORY LIST
    # ==================================================

    def test_category_list_returns_active_categories(
        self,
    ):
        with patch.object(
            CategoryRepository,
            "list_active",
            return_value=[
                self.category,
            ],
        ) as list_mock:
            response = self.client.get(
                self.CATEGORIES_URL
            )

        body = self.assert_success_contract(
            response
        )

        categories = (
            body["data"]["categories"]
        )

        self.assertEqual(
            len(
                categories
            ),
            1,
        )

        self.assertEqual(
            categories[0]["name"],
            "Electronics",
        )

        self.assertEqual(
            body["data"]["count"],
            1,
        )

        list_mock.assert_called_once_with(
            organization=self.organization,
        )

    def test_category_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.CATEGORIES_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_category_collection_creates_category(
        self,
    ):
        payload = {
            "name": "New Category",
            "description": "New category description",
        }

        created_category = Category(
            organization=self.organization,
            name="New Category",
            description="New category description",
            is_active=True,
        )

        with patch.object(
            CategoryAPIService,
            "create_category",
            return_value=created_category,
        ) as create_mock:

            response = self.client.post(
                self.CATEGORIES_URL,
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
            body["data"]["category"]["name"],
            "New Category",
        )

        self.assertEqual(
            body["data"]["category"]["description"],
            "New category description",
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            payload=payload,
        )

    # ==================================================
    # PRODUCT LIST
    # ==================================================

    def test_product_list_uses_query_pipeline(
        self,
    ):
        queryset_marker = object()

        pipeline_result = {
            "items": [
                self.product,
            ],
            "pagination": {
                "page": 2,
                "page_size": 10,
                "total_items": 1,
                "total_pages": 1,
                "has_previous": True,
                "has_next": False,
            },
            "query": {
                "filters": {
                    "is_active": True,
                },
                "search": {
                    "applied": True,
                    "term": "phone",
                    "fields": [
                        "sku",
                        "name",
                        "brand",
                        "barcode",
                    ],
                },
                "sorting": {
                    "fields": [
                        "-selling_price",
                        "id",
                    ],
                    "using_default": False,
                },
            },
        }

        with (
            patch.object(
                ProductRepository,
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
                    f"{self.PRODUCTS_URL}"
                    "?search=phone"
                    "&is_active=true"
                    "&sort=-selling_price"
                    "&page=2"
                    "&page_size=10"
                )
            )

        body = self.assert_success_contract(
            response
        )

        products = (
            body["data"]["products"]
        )

        self.assertEqual(
            len(
                products
            ),
            1,
        )

        self.assertEqual(
            products[0]["sku"],
            "PHONE-001",
        )

        self.assertEqual(
            products[0]["cost_price"],
            "10000.00",
        )

        self.assertEqual(
            products[0]["selling_price"],
            "15000.00",
        )

        self.assertEqual(
            body["data"]["pagination"]["page"],
            2,
        )

        self.assertEqual(
            body["data"]["query"]["search"]["term"],
            "phone",
        )

        queryset_mock.assert_called_once_with(
            organization=self.organization,
        )

        pipeline_mock.assert_called_once()

        called_request = (
            pipeline_mock
            .call_args
            .args[1]
        )

        self.assertEqual(
            called_request.GET["search"],
            "phone",
        )

        self.assertEqual(
            called_request.GET["is_active"],
            "true",
        )

        self.assertEqual(
            called_request.GET["sort"],
            "-selling_price",
        )

        self.assertEqual(
            called_request.GET["page"],
            "2",
        )

    def test_product_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.PRODUCTS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # CREATE
    # ==================================================

    def test_create_product_returns_201(
        self,
    ):
        payload = {
            "sku":
                "phone-001",
            "name":
                "Smart Phone",
            "description":
                "Regression test product.",
            "category_id":
                str(
                    self.category.id
                ),
            "brand":
                "Example Brand",
            "unit":
                "piece",
            "cost_price":
                "10000.00",
            "selling_price":
                "15000.00",
            "barcode":
                "890000000001",
        }

        with patch.object(
            ProductAPIService,
            "create_product",
            return_value=self.product,
        ) as create_mock:
            response = self.client.post(
                self.PRODUCTS_URL,
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        product = (
            body["data"]["product"]
        )

        self.assertEqual(
            product["sku"],
            "PHONE-001",
        )

        self.assertEqual(
            product["name"],
            "Smart Phone",
        )

        self.assertEqual(
            product["category"]["id"],
            str(
                self.category.id
            ),
        )

        self.assertNotIn(
            "organization",
            product,
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            payload=payload,
        )

    def test_create_product_validation_error(
        self,
    ):
        validation_error = (
            ProductAPIValidationError(
                details={
                    "sku": [
                        (
                            "SKU must be unique within "
                            "the current organization."
                        ),
                    ],
                },
            )
        )

        with patch.object(
            ProductAPIService,
            "create_product",
            side_effect=validation_error,
        ):
            response = self.client.post(
                self.PRODUCTS_URL,
                data=json.dumps({
                    "sku": "PHONE-001",
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "sku",
            body["error"]["details"],
        )

    def test_create_product_requires_json_content_type(
        self,
    ):
        response = self.client.post(
            self.PRODUCTS_URL,
            data={
                "sku": "PHONE-001",
            },
        )

        self.assert_error_contract(
            response,
            400,
            "BAD_REQUEST",
        )

    def test_create_product_rejects_invalid_json(
        self,
    ):
        response = self.client.post(
            self.PRODUCTS_URL,
            data="{invalid-json",
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            400,
            "BAD_REQUEST",
        )

    def test_create_product_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.PRODUCTS_URL,
                data=json.dumps({
                    "sku": "PHONE-001",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # DETAIL
    # ==================================================

    def test_product_detail_returns_product(
        self,
    ):
        with patch.object(
            ProductAPIService,
            "get_product",
            return_value=self.product,
        ) as get_mock:
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        product = (
            body["data"]["product"]
        )

        self.assertEqual(
            product["id"],
            str(
                self.product.id
            ),
        )

        self.assertEqual(
            product["sku"],
            "PHONE-001",
        )

        self.assertEqual(
            product["description"],
            "Regression test product.",
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            product_id=str(
                self.product.id
            ),
        )

    def test_cross_tenant_product_is_hidden(
        self,
    ):
        with patch.object(
            ProductAPIService,
            "get_product",
            side_effect=LookupError(
                "Product not found."
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

    def test_product_detail_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.detail_url()
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # UPDATE
    # ==================================================

    def test_update_product_returns_updated_product(
        self,
    ):
        payload = {
            "name":
                "Updated Smart Phone",
            "selling_price":
                "16000.00",
        }

        updated_product = SimpleNamespace(
            **{
                **vars(
                    self.product
                ),
                "name":
                    "Updated Smart Phone",
                "selling_price":
                    Decimal("16000.00"),
            }
        )

        with patch.object(
            ProductAPIService,
            "update_product",
            return_value=updated_product,
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

        product = (
            body["data"]["product"]
        )

        self.assertEqual(
            product["name"],
            "Updated Smart Phone",
        )

        self.assertEqual(
            product["selling_price"],
            "16000.00",
        )

        update_mock.assert_called_once_with(
            organization=self.organization,
            product_id=str(
                self.product.id
            ),
            payload=payload,
        )

    def test_update_product_validation_error(
        self,
    ):
        validation_error = (
            ProductAPIValidationError(
                details={
                    "selling_price": [
                        (
                            "selling_price cannot "
                            "be negative."
                        ),
                    ],
                },
            )
        )

        with patch.object(
            ProductAPIService,
            "update_product",
            side_effect=validation_error,
        ):
            response = self.client.patch(
                self.detail_url(),
                data=json.dumps({
                    "selling_price": "-1",
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "selling_price",
            body["error"]["details"],
        )

    def test_update_product_requires_json_content_type(
        self,
    ):
        response = self.client.patch(
            self.detail_url(),
            data={
                "name": "Updated Product",
            },
        )

        self.assert_error_contract(
            response,
            400,
            "BAD_REQUEST",
        )

    def test_product_detail_rejects_delete(
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
    # QUERY PIPELINE ERRORS
    # ==================================================

    def test_product_list_query_error_uses_contract(
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
                        ),
                    ],
                },
            )
        )

        with (
            patch.object(
                ProductRepository,
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
                    f"{self.PRODUCTS_URL}"
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
    # ACTIVATE
    # ==================================================

    def test_activate_product(
        self,
    ):
        activated_product = SimpleNamespace(
            **{
                **vars(
                    self.product
                ),
                "is_active":
                    True,
            }
        )

        with patch.object(
            ProductAPIService,
            "activate_product",
            return_value=activated_product,
        ) as activate_mock:
            response = self.client.post(
                self.activate_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertTrue(
            body["data"]["product"][
                "is_active"
            ]
        )

        activate_mock.assert_called_once_with(
            organization=self.organization,
            product_id=str(
                self.product.id
            ),
        )

    def test_activate_product_without_permission_is_forbidden(
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

    def test_activate_product_rejects_get(
        self,
    ):
        response = self.client.get(
            self.activate_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # DEACTIVATE
    # ==================================================

    def test_deactivate_product(
        self,
    ):
        deactivated_product = (
            SimpleNamespace(
                **{
                    **vars(
                        self.product
                    ),
                    "is_active":
                        False,
                }
            )
        )

        with patch.object(
            ProductAPIService,
            "deactivate_product",
            return_value=(
                deactivated_product
            ),
        ) as deactivate_mock:
            response = self.client.post(
                self.deactivate_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertFalse(
            body["data"]["product"][
                "is_active"
            ]
        )

        deactivate_mock.assert_called_once_with(
            organization=self.organization,
            product_id=str(
                self.product.id
            ),
        )

    def test_deactivate_missing_product_returns_not_found(
        self,
    ):
        with patch.object(
            ProductAPIService,
            "deactivate_product",
            side_effect=LookupError(
                "Product not found."
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

    # ==================================================
    # SERIALIZATION SAFETY
    # ==================================================

    def test_product_serializer_has_safe_fields(
        self,
    ):
        serialized = (
            ProductAPISerializer
            .serialize_detail(
                self.product
            )
        )

        self.assertEqual(
            serialized["id"],
            str(
                self.product.id
            ),
        )

        self.assertEqual(
            serialized["category"]["id"],
            str(
                self.category.id
            ),
        )

        self.assertEqual(
            serialized["cost_price"],
            "10000.00",
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
            "sku":
                " phone-002 ",
            "name":
                " Test Phone ",
            "category_id":
                str(
                    self.category.id
                ),
            "unit":
                " piece ",
            "cost_price":
                "100.50",
            "selling_price":
                150,
            "brand":
                " Example ",
            "description":
                " Test description ",
            "barcode":
                " 123456 ",
        }

        with patch.object(
            CategoryRepository,
            "get_active_by_id",
            return_value=self.category,
        ):
            values = (
                ProductAPIService
                .validate_create_payload(
                    organization=(
                        self.organization
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            values["sku"],
            "PHONE-002",
        )

        self.assertEqual(
            values["name"],
            "Test Phone",
        )

        self.assertEqual(
            values["unit"],
            "piece",
        )

        self.assertEqual(
            values["cost_price"],
            Decimal("100.50"),
        )

        self.assertEqual(
            values["selling_price"],
            Decimal("150.00"),
        )

        self.assertEqual(
            values["category"],
            self.category,
        )

    def test_service_rejects_cross_tenant_category(
        self,
    ):
        with patch.object(
            CategoryRepository,
            "get_active_by_id",
            return_value=None,
        ):
            with self.assertRaises(
                ProductAPIValidationError
            ) as context:
                (
                    ProductAPIService
                    .validate_create_payload(
                        organization=(
                            self.organization
                        ),
                        payload={
                            "sku":
                                "PHONE-003",
                            "name":
                                "Test Phone",
                            "category_id":
                                str(
                                    ObjectId()
                                ),
                            "unit":
                                "piece",
                        },
                    )
                )

        self.assertIn(
            "category_id",
            context.exception.details,
        )

    def test_service_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            ProductAPIValidationError
        ) as context:
            (
                ProductAPIService
                .validate_update_payload(
                    organization=(
                        self.organization
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

    # ==================================================
    # COLLECTION METHOD RESTRICTION
    # ==================================================

    def test_product_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.PRODUCTS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_category_detail_returns_category(self):
        with patch.object(
            CategoryAPIService,
            "get_category",
            return_value=self.category,
        ) as get_mock:

            response = self.client.get(
                f"{self.CATEGORIES_URL}{self.category.id}/"
            )

        body = self.assert_success_contract(response)

        category = body["data"]["category"]

        self.assertEqual(category["id"], str(self.category.id))
        self.assertEqual(category["name"], "Electronics")
        self.assertEqual(
            category["description"],
            "Electronic products.",
        )
        self.assertTrue(category["is_active"])

        get_mock.assert_called_once_with(
            organization=self.organization,
            category_id=str(self.category.id),
        )


    def test_category_detail_without_permission_is_forbidden(self):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                f"{self.CATEGORIES_URL}{self.category.id}/"
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_category_detail_updates_category(self):
        payload = {
            "name": "Updated Electronics",
            "description": "Updated electronic products.",
        }

        updated_category = Category(
            id=self.category.id,
            organization=self.organization,
            name="Updated Electronics",
            description="Updated electronic products.",
            is_active=True,
        )

        with patch.object(
            CategoryAPIService,
            "update_category",
            return_value=updated_category,
        ) as update_mock:

            response = self.client.patch(
                f"{self.CATEGORIES_URL}{self.category.id}/",
                data=json.dumps(payload),
                content_type="application/json",
            )

        body = self.assert_success_contract(response)

        category = body["data"]["category"]

        self.assertEqual(category["name"], "Updated Electronics")
        self.assertEqual(
            category["description"],
            "Updated electronic products.",
        )

        update_mock.assert_called_once_with(
            organization=self.organization,
            category_id=str(self.category.id),
            payload=payload,
        )


    def test_category_detail_update_without_permission_is_forbidden(self):
        payload = {
            "name": "Updated Electronics",
        }

        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.patch(
                f"{self.CATEGORIES_URL}{self.category.id}/",
                data=json.dumps(payload),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )


    def test_category_detail_update_not_found(self):
        payload = {
            "name": "Updated Electronics",
        }

        with patch.object(
            CategoryAPIService,
            "update_category",
            side_effect=LookupError("Category not found."),
        ):
            response = self.client.patch(
                f"{self.CATEGORIES_URL}507f1f77bcf86cd799439011/",
                data=json.dumps(payload),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_category_activate(self):
        activated_category = Category(
            id=self.category.id,
            organization=self.organization,
            name="Electronics",
            description="Electronic products.",
            is_active=True,
        )

        with patch.object(
            CategoryAPIService,
            "activate_category",
            return_value=activated_category,
        ) as activate_mock:

            response = self.client.post(
                f"{self.CATEGORIES_URL}{self.category.id}/activate/"
            )

        body = self.assert_success_contract(response)

        category = body["data"]["category"]

        self.assertTrue(category["is_active"])
        self.assertEqual(category["name"], "Electronics")

        activate_mock.assert_called_once_with(
            organization=self.organization,
            category_id=str(self.category.id),
        )


    def test_category_activate_without_permission_is_forbidden(self):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                f"{self.CATEGORIES_URL}{self.category.id}/activate/"
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )


    def test_category_deactivate(self):
        deactivated_category = Category(
            id=self.category.id,
            organization=self.organization,
            name="Electronics",
            description="Electronic products.",
            is_active=False,
        )

        with patch.object(
            CategoryAPIService,
            "deactivate_category",
            return_value=deactivated_category,
        ) as deactivate_mock:

            response = self.client.post(
                f"{self.CATEGORIES_URL}{self.category.id}/deactivate/"
            )

        body = self.assert_success_contract(response)

        category = body["data"]["category"]

        self.assertFalse(category["is_active"])
        self.assertEqual(category["name"], "Electronics")

        deactivate_mock.assert_called_once_with(
            organization=self.organization,
            category_id=str(self.category.id),
        )


    def test_category_deactivate_without_permission_is_forbidden(self):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                f"{self.CATEGORIES_URL}{self.category.id}/deactivate/"
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )