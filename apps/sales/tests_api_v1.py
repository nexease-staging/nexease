import json

from datetime import datetime, timedelta
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
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.sales.api.v1.serializers import (
    AccountsReceivableAPISerializer,
    BankAccountLookupAPISerializer,
    CustomerAPISerializer,
    CustomerPaymentAPISerializer,
    InvoiceAPISerializer,
    SalesOrderAPISerializer,
    CreditNoteAPISerializer,
    SalesReturnAPISerializer,
)
from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.sales.repositories.payment_repository import (
    PaymentRepository,
)
from apps.sales.services.invoice_api_service import (
    InvoiceAPIService,
    InvoiceAPIStateError,
    InvoiceAPIValidationError,
)
from apps.sales.services.customer_payment_api_service import (
    CustomerPaymentAPIService,
    CustomerPaymentAPIValidationError,
)
from apps.sales.services.invoice_service import (
    InvoiceService,
)
from apps.sales.services.payment_service import (
    PaymentService,
)
from apps.sales.repositories.customer_repository import (
    CustomerRepository,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.repositories.credit_note_repository import (
    CreditNoteRepository,
)
from apps.sales.repositories.sales_return_repository import (
    SalesReturnRepository,
)
from apps.sales.services.customer_api_service import (
    CustomerAPIService,
    CustomerAPIStateError,
    CustomerAPIValidationError,
)
from apps.sales.services.sales_order_api_service import (
    SalesOrderAPIService,
    SalesOrderAPIStateError,
    SalesOrderAPIValidationError,
)
from apps.sales.services.credit_note_api_service import (
    CreditNoteAPIService,
    CreditNoteAPIStateError,
    CreditNoteAPIValidationError,
)
from apps.sales.services.sales_return_api_service import (
    SalesReturnAPIService,
    SalesReturnAPIStateError,
    SalesReturnAPIValidationError,
)
from apps.sales.services.sales_order_service import (
    SalesOrderService,
)
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)

class CustomerAPIV1RegressionTestCase(
    SimpleTestCase
):

    CUSTOMERS_URL = (
        "/api/v1/customers/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Customer Regression Organization",
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

        self.customer = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            code="CUST-001",
            name="Regression Customer",
            email="customer@example.com",
            phone="9999999998",
            gstin="27ABCDE1234F1Z5",
            billing_address="Billing Address",
            shipping_address="Shipping Address",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            pincode="400001",
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
        customer=None,
    ):
        customer = (
            customer
            or
            self.customer
        )

        return (
            f"{self.CUSTOMERS_URL}"
            f"{customer.id}/"
        )

    def activate_url(
        self,
        customer=None,
    ):
        customer = (
            customer
            or
            self.customer
        )

        return (
            f"{self.CUSTOMERS_URL}"
            f"{customer.id}/activate/"
        )

    def deactivate_url(
        self,
        customer=None,
    ):
        customer = (
            customer
            or
            self.customer
        )

        return (
            f"{self.CUSTOMERS_URL}"
            f"{customer.id}/deactivate/"
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

    def test_anonymous_customer_list_is_rejected(
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
                self.CUSTOMERS_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    # ==================================================
    # LIST
    # ==================================================

    def test_customer_list_uses_query_pipeline(
        self,
    ):
        with (
            patch.object(
                CustomerRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value={
                    "items": [
                        self.customer,
                    ],
                    "pagination": {
                        "page": 1,
                        "page_size": 25,
                        "total_items": 1,
                        "total_pages": 1,
                        "has_next": False,
                        "has_previous": False,
                    },
                    "query": {
                        "search": None,
                        "filters": {},
                        "sort": [
                            "name",
                            "id",
                        ],
                    },
                },
            ) as pipeline_mock,
        ):
            response = self.client.get(
                (
                    f"{self.CUSTOMERS_URL}"
                    "?search=Regression"
                    "&is_active=true"
                    "&sort=name"
                )
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["customers"][0][
                "code"
            ],
            "CUST-001",
        )

        pipeline_mock.assert_called_once()

    def test_customer_list_query_error_uses_contract(
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
                CustomerRepository,
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
                    f"{self.CUSTOMERS_URL}"
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

    def test_customer_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.CUSTOMERS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # CREATE
    # ==================================================

    def test_create_customer(
        self,
    ):
        with patch.object(
            CustomerAPIService,
            "create_customer",
            return_value=self.customer,
        ) as create_mock:
            response = self.client.post(
                self.CUSTOMERS_URL,
                data=json.dumps({
                    "code":
                        "CUST-001",
                    "name":
                        "Regression Customer",
                    "email":
                        "customer@example.com",
                }),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"]["customer"][
                "code"
            ],
            "CUST-001",
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            payload={
                "code":
                    "CUST-001",
                "name":
                    "Regression Customer",
                "email":
                    "customer@example.com",
            },
        )

    def test_create_customer_validation_error(
        self,
    ):
        with patch.object(
            CustomerAPIService,
            "create_customer",
            side_effect=(
                CustomerAPIValidationError(
                    details={
                        "code": [
                            (
                                "Customer code is "
                                "required."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.post(
                self.CUSTOMERS_URL,
                data=json.dumps({
                    "name":
                        "Regression Customer",
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

    def test_customer_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.CUSTOMERS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # DETAIL
    # ==================================================

    def test_customer_detail(
        self,
    ):
        with patch.object(
            CustomerAPIService,
            "get_customer",
            return_value=self.customer,
        ):
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["customer"][
                "billing_address"
            ],
            "Billing Address",
        )

    def test_missing_customer_returns_not_found(
        self,
    ):
        with patch.object(
            CustomerAPIService,
            "get_customer",
            side_effect=LookupError(
                "Customer not found."
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

    def test_malformed_customer_id_is_validation_error(
        self,
    ):
        response = self.client.get(
            (
                f"{self.CUSTOMERS_URL}"
                "invalid-id/"
            )
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "customer_id",
            body["error"]["details"],
        )

    # ==================================================
    # UPDATE
    # ==================================================

    def test_update_customer(
        self,
    ):
        updated_customer = SimpleNamespace(
            **{
                **vars(
                    self.customer
                ),
                "name":
                    "Updated Customer",
            }
        )

        with patch.object(
            CustomerAPIService,
            "update_customer",
            return_value=updated_customer,
        ) as update_mock:
            response = self.client.patch(
                self.detail_url(),
                data=json.dumps({
                    "name":
                        "Updated Customer",
                }),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["customer"]["name"],
            "Updated Customer",
        )

        update_mock.assert_called_once_with(
            organization=self.organization,
            customer_id=str(
                self.customer.id
            ),
            payload={
                "name":
                    "Updated Customer",
            },
        )

    def test_inactive_customer_update_is_unprocessable(
        self,
    ):
        with patch.object(
            CustomerAPIService,
            "update_customer",
            side_effect=(
                CustomerAPIStateError(
                    message=(
                        "Inactive customers cannot "
                        "be updated."
                    ),
                    details={
                        "is_active": [
                            (
                                "Activate the customer "
                                "before updating it."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.patch(
                self.detail_url(),
                data=json.dumps({
                    "name":
                        "Updated Customer",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    # ==================================================
    # LIFECYCLE
    # ==================================================

    def test_activate_customer(
        self,
    ):
        with patch.object(
            CustomerAPIService,
            "activate_customer",
            return_value=self.customer,
        ):
            response = self.client.post(
                self.activate_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_success_contract(
            response
        )

    def test_deactivate_customer(
        self,
    ):
        deactivated_customer = (
            SimpleNamespace(
                **{
                    **vars(
                        self.customer
                    ),
                    "is_active":
                        False,
                }
            )
        )

        with patch.object(
            CustomerAPIService,
            "deactivate_customer",
            return_value=(
                deactivated_customer
            ),
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
            body["data"]["customer"][
                "is_active"
            ]
        )


    # ==================================================
    # SERIALIZATION SAFETY
    # ==================================================

    def test_customer_serializer_has_safe_fields(
        self,
    ):
        serialized = (
            CustomerAPISerializer
            .serialize_detail(
                self.customer
            )
        )

        self.assertEqual(
            serialized["id"],
            str(
                self.customer.id
            ),
        )

        self.assertEqual(
            serialized["code"],
            "CUST-001",
        )

        self.assertEqual(
            serialized["billing_address"],
            "Billing Address",
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
        with patch.object(
            CustomerRepository,
            "code_exists",
            return_value=False,
        ):
            values = (
                CustomerAPIService
                .validate_create_payload(
                    organization=(
                        self.organization
                    ),
                    payload={
                        "code":
                            " cust-002 ",
                        "name":
                            " Test Customer ",
                        "email":
                            " CUSTOMER@EXAMPLE.COM ",
                        "phone":
                            " 9999999997 ",
                        "gstin":
                            " 27abcde1234f1z5 ",
                        "country":
                            " India ",
                    },
                )
            )

        self.assertEqual(
            values["code"],
            "CUST-002",
        )

        self.assertEqual(
            values["name"],
            "Test Customer",
        )

        self.assertEqual(
            values["email"],
            "customer@example.com",
        )

        self.assertEqual(
            values["gstin"],
            "27ABCDE1234F1Z5",
        )

        self.assertEqual(
            values["country"],
            "India",
        )

    def test_service_rejects_duplicate_code(
        self,
    ):
        with patch.object(
            CustomerRepository,
            "code_exists",
            return_value=True,
        ):
            with self.assertRaises(
                CustomerAPIValidationError
            ) as context:
                (
                    CustomerAPIService
                    .validate_create_payload(
                        organization=(
                            self.organization
                        ),
                        payload={
                            "code":
                                "CUST-001",
                            "name":
                                "Duplicate Customer",
                        },
                    )
                )

        self.assertIn(
            "code",
            context.exception.details,
        )

    def test_service_rejects_code_update(
        self,
    ):
        with self.assertRaises(
            CustomerAPIValidationError
        ) as context:
            (
                CustomerAPIService
                .validate_update_payload(
                    payload={
                        "code":
                            "CHANGED-CODE",
                    },
                )
            )

        self.assertIn(
            "code",
            context.exception.details,
        )

    def test_service_rejects_invalid_email(
        self,
    ):
        with patch.object(
            CustomerRepository,
            "code_exists",
            return_value=False,
        ):
            with self.assertRaises(
                CustomerAPIValidationError
            ) as context:
                (
                    CustomerAPIService
                    .validate_create_payload(
                        organization=(
                            self.organization
                        ),
                        payload={
                            "code":
                                "CUST-003",
                            "name":
                                "Invalid Email Customer",
                            "email":
                                "not-an-email",
                        },
                    )
                )

        self.assertIn(
            "email",
            context.exception.details,
        )

    def test_service_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            CustomerAPIValidationError
        ) as context:
            (
                CustomerAPIService
                .validate_update_payload(
                    payload={
                        "organization_id":
                            str(
                                ObjectId()
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

class SalesOrderAPIV1RegressionTestCase(
    SimpleTestCase
):

    SALES_ORDERS_URL = (
        "/api/v1/sales-orders/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Sales Order Organization",
            email="sales-orders@example.com",
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

        self.customer = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            code="CUST-001",
            name="Sales Order Customer",
            email="customer@example.com",
            phone="9999999999",
            gstin="27ABCDE1234F1Z5",
            billing_address="Billing Address",
            shipping_address="Shipping Address",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            pincode="400001",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.warehouse = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            code="MAIN-001",
            name="Main Warehouse",
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

        self.sales_order_item = (
            SimpleNamespace(
                product=self.product,
                quantity=Decimal("2.00"),
                fulfilled_quantity=(
                    Decimal("0.00")
                ),
                unit_price=Decimal("100.00"),
                tax_rate=Decimal("18.00"),
                discount=Decimal("10.00"),
                line_subtotal=(
                    Decimal("200.00")
                ),
                line_tax=Decimal("34.20"),
                line_total=Decimal("224.20"),
            )
        )

        self.sales_order = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            so_number="SO-TEST000001",
            customer=self.customer,
            warehouse=self.warehouse,
            status="DRAFT",
            order_date=now,
            expected_delivery_date=now,
            items=[
                self.sales_order_item,
            ],
            subtotal=Decimal("200.00"),
            tax_amount=Decimal("34.20"),
            discount_amount=Decimal("10.00"),
            total_amount=Decimal("224.20"),
            notes="Regression sales order.",
            created_by=self.user,
            confirmed_at=None,
            fulfilled_at=None,
            cancelled_at=None,
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
        sales_order=None,
    ):
        sales_order = (
            sales_order
            or
            self.sales_order
        )

        return (
            f"{self.SALES_ORDERS_URL}"
            f"{sales_order.id}/"
        )

    def confirm_url(
        self,
        sales_order=None,
    ):
        sales_order = (
            sales_order
            or
            self.sales_order
        )

        return (
            f"{self.SALES_ORDERS_URL}"
            f"{sales_order.id}/confirm/"
        )

    def cancel_url(
        self,
        sales_order=None,
    ):
        sales_order = (
            sales_order
            or
            self.sales_order
        )

        return (
            f"{self.SALES_ORDERS_URL}"
            f"{sales_order.id}/cancel/"
        )

    def fulfill_url(
        self,
        sales_order=None,
    ):
        sales_order = (
            sales_order
            or
            self.sales_order
        )

        return (
            f"{self.SALES_ORDERS_URL}"
            f"{sales_order.id}/fulfill/"
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
    # AUTHENTICATION AND COLLECTION
    # ==================================================

    def test_anonymous_sales_order_list_is_rejected(
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
                self.SALES_ORDERS_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    def test_sales_order_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.SALES_ORDERS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_sales_order_list_uses_query_pipeline(
        self,
    ):
        pipeline_result = {
            "items": [
                self.sales_order,
            ],
            "pagination": {
                "page": 1,
                "page_size": 25,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": None,
                "filters": {},
                "sort": [
                    "-created_at",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                SalesOrderRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ) as pipeline_mock,
        ):
            response = self.client.get(
                (
                    f"{self.SALES_ORDERS_URL}"
                    "?status=DRAFT"
                )
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            len(
                body["data"][
                    "sales_orders"
                ]
            ),
            1,
        )

        self.assertEqual(
            body["data"]["sales_orders"][0][
                "so_number"
            ],
            self.sales_order.so_number,
        )

        pipeline_mock.assert_called_once()

    def test_sales_order_list_query_error_uses_contract(
        self,
    ):
        pipeline_error = (
            APIQueryPipelineError(
                component="filtering",
                message=(
                    "Invalid filter value."
                ),
                details={
                    "customer_id": [
                        (
                            "Enter a valid "
                            "identifier."
                        ),
                    ],
                },
            )
        )

        with (
            patch.object(
                SalesOrderRepository,
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
                    f"{self.SALES_ORDERS_URL}"
                    "?customer_id=invalid-id"
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
    # CREATE
    # ==================================================

    def test_create_sales_order(
        self,
    ):
        payload = {
            "customer_id":
                str(
                    self.customer.id
                ),
            "warehouse_id":
                str(
                    self.warehouse.id
                ),
            "order_date":
                "2026-08-28T10:00:00",
            "expected_delivery_date":
                "2026-08-30T10:00:00",
            "items": [
                {
                    "product_id":
                        str(
                            self.product.id
                        ),
                    "quantity":
                        "2.00",
                    "unit_price":
                        "100.00",
                    "tax_rate":
                        "18.00",
                    "discount":
                        "10.00",
                },
            ],
            "notes":
                "Regression sales order.",
        }

        with patch.object(
            SalesOrderAPIService,
            "create_sales_order",
            return_value=self.sales_order,
        ) as create_mock:
            response = self.client.post(
                self.SALES_ORDERS_URL,
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"]["sales_order"][
                "total_amount"
            ],
            "224.20",
        )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            payload=payload,
        )

    def test_create_sales_order_validation_error(
        self,
    ):
        with patch.object(
            SalesOrderAPIService,
            "create_sales_order",
            side_effect=(
                SalesOrderAPIValidationError(
                    details={
                        "items": [
                            (
                                "At least one item "
                                "is required."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.post(
                self.SALES_ORDERS_URL,
                data=json.dumps({
                    "items": [],
                }),
                content_type="application/json",
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "items",
            body["error"]["details"],
        )

    # ==================================================
    # DETAIL AND UPDATE
    # ==================================================

    def test_sales_order_detail(
        self,
    ):
        with patch.object(
            SalesOrderAPIService,
            "get_sales_order",
            return_value=self.sales_order,
        ):
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["sales_order"][
                "so_number"
            ],
            self.sales_order.so_number,
        )

        self.assertEqual(
            len(
                body["data"]["sales_order"][
                    "items"
                ]
            ),
            1,
        )

    def test_missing_sales_order_returns_not_found(
        self,
    ):
        with patch.object(
            SalesOrderAPIService,
            "get_sales_order",
            side_effect=LookupError(
                "Sales order not found."
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

    def test_malformed_sales_order_id_is_validation_error(
        self,
    ):
        response = self.client.get(
            (
                f"{self.SALES_ORDERS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_update_sales_order(
        self,
    ):
        payload = {
            "notes":
                "Updated notes.",
        }

        with patch.object(
            SalesOrderAPIService,
            "update_sales_order",
            return_value=self.sales_order,
        ) as update_mock:
            response = self.client.put(
                self.detail_url(),
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        self.assert_success_contract(
            response
        )

        update_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            sales_order_id=str(
                self.sales_order.id
            ),
            payload=payload,
        )

    def test_confirmed_sales_order_update_is_unprocessable(
        self,
    ):
        with patch.object(
            SalesOrderAPIService,
            "update_sales_order",
            side_effect=(
                SalesOrderAPIStateError(
                    message=(
                        "Only draft sales orders "
                        "can be edited."
                    ),
                    details={
                        "status": [
                            (
                                "Editing is not "
                                "allowed."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.put(
                self.detail_url(),
                data=json.dumps({
                    "notes":
                        "Invalid update.",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    # ==================================================
    # CONFIRM
    # ==================================================

    def test_confirm_sales_order(
        self,
    ):
        confirmed_order = SimpleNamespace(
            **{
                **vars(
                    self.sales_order
                ),
                "status":
                    "CONFIRMED",
                "confirmed_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            SalesOrderAPIService,
            "confirm_sales_order",
            return_value=confirmed_order,
        ) as confirm_mock:
            response = self.client.post(
                self.confirm_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["sales_order"][
                "status"
            ],
            "CONFIRMED",
        )

        confirm_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            sales_order_id=str(
                self.sales_order.id
            ),
        )

    def test_confirm_sales_order_state_error(
        self,
    ):
        with patch.object(
            SalesOrderAPIService,
            "confirm_sales_order",
            side_effect=(
                SalesOrderAPIStateError(
                    message=(
                        "Only draft sales orders "
                        "can be confirmed."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.confirm_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_confirm_sales_order_rejects_get(
        self,
    ):
        response = self.client.get(
            self.confirm_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # CANCEL
    # ==================================================

    def test_cancel_sales_order(
        self,
    ):
        cancelled_order = SimpleNamespace(
            **{
                **vars(
                    self.sales_order
                ),
                "status":
                    "CANCELLED",
                "cancelled_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            SalesOrderAPIService,
            "cancel_sales_order",
            return_value=cancelled_order,
        ) as cancel_mock:
            response = self.client.post(
                self.cancel_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["sales_order"][
                "status"
            ],
            "CANCELLED",
        )

        cancel_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            sales_order_id=str(
                self.sales_order.id
            ),
        )

    def test_cancel_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.cancel_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    # ==================================================
    # FULFILMENT
    # ==================================================

    def test_fulfill_sales_order(
        self,
    ):
        fulfilled_item = SimpleNamespace(
            **{
                **vars(
                    self.sales_order_item
                ),
                "fulfilled_quantity":
                    Decimal("2.00"),
            }
        )

        fulfilled_order = SimpleNamespace(
            **{
                **vars(
                    self.sales_order
                ),
                "status":
                    "FULFILLED",
                "items": [
                    fulfilled_item,
                ],
                "fulfilled_at":
                    datetime.utcnow(),
            }
        )

        payload = {
            "items": [
                {
                    "product_id":
                        str(
                            self.product.id
                        ),
                    "quantity":
                        "2.00",
                },
            ],
            "notes":
                "Dispatched.",
        }

        with patch.object(
            SalesOrderAPIService,
            "fulfill_sales_order",
            return_value=fulfilled_order,
        ) as fulfill_mock:
            response = self.client.post(
                self.fulfill_url(),
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["sales_order"][
                "status"
            ],
            "FULFILLED",
        )

        self.assertEqual(
            body["data"]["sales_order"][
                "items"
            ][0]["remaining_quantity"],
            "0.00",
        )

        fulfill_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            sales_order_id=str(
                self.sales_order.id
            ),
            payload=payload,
        )

    def test_fulfill_sales_order_validation_error(
        self,
    ):
        with patch.object(
            SalesOrderAPIService,
            "fulfill_sales_order",
            side_effect=(
                SalesOrderAPIValidationError(
                    details={
                        "items": [
                            (
                                "At least one item "
                                "is required."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.post(
                self.fulfill_url(),
                data=json.dumps({
                    "items": [],
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    # ==================================================
    # SERIALIZATION
    # ==================================================

    def test_sales_order_serializer_has_safe_fields(
        self,
    ):
        serialized = (
            SalesOrderAPISerializer
            .serialize_detail(
                self.sales_order
            )
        )

        self.assertEqual(
            serialized["id"],
            str(
                self.sales_order.id
            ),
        )

        self.assertEqual(
            serialized["customer"]["id"],
            str(
                self.customer.id
            ),
        )

        self.assertEqual(
            serialized["warehouse"]["id"],
            str(
                self.warehouse.id
            ),
        )

        self.assertEqual(
            serialized["items"][0][
                "product"
            ]["id"],
            str(
                self.product.id
            ),
        )

        self.assertEqual(
            serialized["total_amount"],
            "224.20",
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
    # SERVICE VALIDATION
    # ==================================================

    def test_service_normalizes_create_payload(
        self,
    ):
        payload = {
            "customer_id":
                str(
                    self.customer.id
                ),
            "warehouse_id":
                str(
                    self.warehouse.id
                ),
            "order_date":
                "2026-08-28T10:00:00",
            "expected_delivery_date":
                "2026-08-30T10:00:00",
            "items": [
                {
                    "product_id":
                        str(
                            self.product.id
                        ),
                    "quantity":
                        "2.00",
                    "unit_price":
                        100,
                    "tax_rate":
                        "18.00",
                    "discount":
                        "10.00",
                },
            ],
            "notes":
                " Test order ",
        }

        with (
            patch.object(
                CustomerRepository,
                "get_by_id",
                return_value=self.customer,
            ),
            patch.object(
                WarehouseRepository,
                "get_by_id",
                return_value=self.warehouse,
            ),
            patch.object(
                ProductRepository,
                "get_by_id",
                return_value=self.product,
            ),
        ):
            values = (
                SalesOrderAPIService
                .validate_create_payload(
                    organization=(
                        self.organization
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            values["customer"],
            self.customer,
        )

        self.assertEqual(
            values["warehouse"],
            self.warehouse,
        )

        self.assertEqual(
            values["raw_items"][0][
                "quantity"
            ],
            Decimal("2.00"),
        )

        self.assertEqual(
            values["raw_items"][0][
                "unit_price"
            ],
            Decimal("100"),
        )

        self.assertEqual(
            values["notes"],
            "Test order",
        )

    def test_service_rejects_cross_tenant_customer(
        self,
    ):
        with patch.object(
            CustomerRepository,
            "get_by_id",
            return_value=None,
        ):
            with self.assertRaises(
                SalesOrderAPIValidationError
            ) as context:
                (
                    SalesOrderAPIService
                    .validate_create_payload(
                        organization=(
                            self.organization
                        ),
                        payload={
                            "customer_id":
                                str(
                                    ObjectId()
                                ),
                            "warehouse_id":
                                str(
                                    self.warehouse.id
                                ),
                            "order_date":
                                "2026-08-28",
                            "items": [
                                {
                                    "product_id":
                                        str(
                                            self.product.id
                                        ),
                                    "quantity":
                                        "1.00",
                                    "unit_price":
                                        "100.00",
                                },
                            ],
                        },
                    )
                )

        self.assertIn(
            "customer_id",
            context.exception.details,
        )

    def test_service_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            SalesOrderAPIValidationError
        ) as context:
            (
                SalesOrderAPIService
                .validate_update_payload(
                    organization=(
                        self.organization
                    ),
                    sales_order=(
                        self.sales_order
                    ),
                    payload={
                        "status":
                            "CONFIRMED",
                        "total_amount":
                            "1.00",
                    },
                )
            )

        self.assertIn(
            "status",
            context.exception.details,
        )

        self.assertIn(
            "total_amount",
            context.exception.details,
        )

    # ==================================================
    # METHOD RESTRICTION
    # ==================================================

    def test_sales_order_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.SALES_ORDERS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

class InvoiceAPIV1RegressionTestCase(
    SimpleTestCase
):

    INVOICES_URL = (
        "/api/v1/invoices/"
    )

    BANK_ACCOUNTS_URL = (
        "/api/v1/invoice-bank-accounts/"
    )
    CUSTOMER_PAYMENTS_URL = (
        "/api/v1/customer-payments/"
    )

    ACCOUNTS_RECEIVABLE_URL = (
        "/api/v1/accounts-receivable/"
    )

    RECEIVABLE_AGING_URL = (
        (
            "/api/v1/"
            "accounts-receivable/aging/"
        )
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Invoice Organization",
            email="invoices@example.com",
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

        self.customer = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            code="CUST-INV-001",
            name="Invoice Customer",
            email="customer@example.com",
            phone="9999999999",
            gstin="27ABCDE1234F1Z5",
            billing_address="Billing Address",
            shipping_address="Shipping Address",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            pincode="400001",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.warehouse = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            code="MAIN-001",
            name="Main Warehouse",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            is_active=True,
        )

        self.product = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            sku="PHONE-INV-001",
            name="Invoice Phone",
            unit="piece",
            is_active=True,
        )

        self.sales_order_item = (
            SimpleNamespace(
                product=self.product,
                quantity=Decimal("2.00"),
                fulfilled_quantity=(
                    Decimal("2.00")
                ),
                unit_price=Decimal("100.00"),
                tax_rate=Decimal("18.00"),
                discount=Decimal("10.00"),
                line_subtotal=(
                    Decimal("200.00")
                ),
                line_tax=Decimal("34.20"),
                line_total=Decimal("224.20"),
            )
        )

        self.sales_order = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            so_number="SO-INVOICE-001",
            customer=self.customer,
            warehouse=self.warehouse,
            status="FULFILLED",
            items=[
                self.sales_order_item,
            ],
            created_at=now,
            updated_at=now,
        )

        self.invoice_item = (
            SimpleNamespace(
                product=self.product,
                quantity=Decimal("2.00"),
                unit_price=Decimal("100.00"),
                tax_rate=Decimal("18.00"),
                discount=Decimal("10.00"),
                line_subtotal=(
                    Decimal("200.00")
                ),
                line_tax=Decimal("34.20"),
                line_total=Decimal("224.20"),
            )
        )

        self.invoice = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            invoice_number="INV-TEST000001",
            sales_order=self.sales_order,
            customer=self.customer,
            status="DRAFT",
            invoice_date=now,
            due_date=now,
            items=[
                self.invoice_item,
            ],
            subtotal=Decimal("200.00"),
            tax_amount=Decimal("34.20"),
            discount_amount=Decimal("10.00"),
            total_amount=Decimal("224.20"),
            amount_paid=Decimal("0.00"),
            balance_due=Decimal("224.20"),
            billing_name=self.customer.name,
            billing_address=(
                self.customer.billing_address
            ),
            billing_city=self.customer.city,
            billing_state=self.customer.state,
            billing_country=(
                self.customer.country
            ),
            billing_pincode=(
                self.customer.pincode
            ),
            customer_gstin=(
                self.customer.gstin
            ),
            notes="Regression invoice.",
            created_by=self.user,
            issued_at=None,
            paid_at=None,
            cancelled_at=None,
            created_at=now,
            updated_at=now,
        )

        self.bank_account = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            account_name="Main Bank",
            account_type="BANK",
            bank_name="Test Bank",
            account_number="1234567890",
            ifsc_code="TEST0000001",
            currency="INR",
            current_balance=Decimal("1000.00"),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.payment_allocation = (
            SimpleNamespace(
                invoice=self.invoice,
                amount=Decimal("100.00"),
            )
        )

        self.payment = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            payment_number="PAY-TEST000001",
            customer=self.customer,
            payment_date=now,
            amount=Decimal("100.00"),
            payment_method="BANK_TRANSFER",
            bank_account=self.bank_account,
            reference_number="UTR-001",
            allocations=[
                self.payment_allocation,
            ],
            notes="Regression payment.",
            created_by=self.user,
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

    def payment_detail_url(
        self,
        payment=None,
    ):
        payment = (
            payment
            or
            self.payment
        )

        return (
            f"{self.CUSTOMER_PAYMENTS_URL}"
            f"{payment.id}/"
        )
    def detail_url(self):
        return (
            f"{self.INVOICES_URL}"
            f"{self.invoice.id}/"
        )

    def issue_url(self):
        return (
            f"{self.INVOICES_URL}"
            f"{self.invoice.id}/issue/"
        )

    def cancel_url(self):
        return (
            f"{self.INVOICES_URL}"
            f"{self.invoice.id}/cancel/"
        )

    def payment_url(self):
        return (
            f"{self.INVOICES_URL}"
            f"{self.invoice.id}/"
            "record-payment/"
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

        return body

    def test_anonymous_invoice_list_is_rejected(
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
                self.INVOICES_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    def test_invoice_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.INVOICES_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_invoice_list_uses_query_pipeline(
        self,
    ):
        pipeline_result = {
            "items": [
                self.invoice,
            ],
            "pagination": {
                "page": 1,
                "page_size": 25,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": None,
                "filters": {},
                "sort": [
                    "-created_at",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                InvoiceRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ) as pipeline_mock,
        ):
            response = self.client.get(
                (
                    f"{self.INVOICES_URL}"
                    "?status=DRAFT"
                )
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["invoices"][0][
                "invoice_number"
            ],
            self.invoice.invoice_number,
        )

        pipeline_mock.assert_called_once()

    def test_invoice_list_query_error_uses_contract(
        self,
    ):
        pipeline_error = (
            APIQueryPipelineError(
                component="filtering",
                message="Invalid filter.",
                details={
                    "customer_id": [
                        "Invalid identifier.",
                    ],
                },
            )
        )

        with (
            patch.object(
                InvoiceRepository,
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
                    f"{self.INVOICES_URL}"
                    "?customer_id=invalid"
                )
            )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_create_invoice(
        self,
    ):
        payload = {
            "sales_order_id":
                str(
                    self.sales_order.id
                ),
            "invoice_date":
                "2026-08-29",
            "due_date":
                "2026-09-28",
            "notes":
                "Regression invoice.",
        }

        with patch.object(
            InvoiceAPIService,
            "create_invoice",
            return_value=self.invoice,
        ) as create_mock:
            response = self.client.post(
                self.INVOICES_URL,
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"]["invoice"][
                "total_amount"
            ],
            "224.20",
        )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            payload=payload,
        )

    def test_create_invoice_state_error(
        self,
    ):
        with patch.object(
            InvoiceAPIService,
            "create_invoice",
            side_effect=(
                InvoiceAPIStateError(
                    message=(
                        "Invoice can only be "
                        "generated from a fulfilled "
                        "Sales Order."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.INVOICES_URL,
                data=json.dumps({
                    "sales_order_id":
                        str(
                            self.sales_order.id
                        ),
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_invoice_detail(
        self,
    ):
        with patch.object(
            InvoiceAPIService,
            "get_invoice",
            return_value=self.invoice,
        ):
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["invoice"][
                "invoice_number"
            ],
            self.invoice.invoice_number,
        )

    def test_missing_invoice_returns_not_found(
        self,
    ):
        with patch.object(
            InvoiceAPIService,
            "get_invoice",
            side_effect=LookupError(
                "Invoice not found."
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

    def test_malformed_invoice_id_is_validation_error(
        self,
    ):
        response = self.client.get(
            (
                f"{self.INVOICES_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_active_bank_account_lookup(
        self,
    ):
        with patch.object(
            InvoiceAPIService,
            "list_active_bank_accounts",
            return_value=[
                self.bank_account,
            ],
        ):
            response = self.client.get(
                self.BANK_ACCOUNTS_URL
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["count"],
            1,
        )

        self.assertEqual(
            body["data"]["bank_accounts"][0][
                "masked_account_number"
            ],
            "••••7890",
        )

    def test_issue_invoice(
        self,
    ):
        issued_invoice = SimpleNamespace(
            **{
                **vars(
                    self.invoice
                ),
                "status":
                    "ISSUED",
                "issued_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            InvoiceAPIService,
            "issue_invoice",
            return_value=issued_invoice,
        ) as issue_mock:
            response = self.client.post(
                self.issue_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["invoice"]["status"],
            "ISSUED",
        )

        issue_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            invoice_id=str(
                self.invoice.id
            ),
        )

    def test_issue_invoice_state_error(
        self,
    ):
        with patch.object(
            InvoiceAPIService,
            "issue_invoice",
            side_effect=(
                InvoiceAPIStateError(
                    message=(
                        "Only draft invoices "
                        "can be issued."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.issue_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_cancel_invoice(
        self,
    ):
        cancelled_invoice = SimpleNamespace(
            **{
                **vars(
                    self.invoice
                ),
                "status":
                    "CANCELLED",
                "cancelled_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            InvoiceAPIService,
            "cancel_invoice",
            return_value=cancelled_invoice,
        ):
            response = self.client.post(
                self.cancel_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["invoice"]["status"],
            "CANCELLED",
        )

    def test_cancel_invoice_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.cancel_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_record_invoice_payment(
        self,
    ):
        payload = {
            "amount":
                "100.00",
            "payment_method":
                "BANK_TRANSFER",
            "bank_account_id":
                str(
                    self.bank_account.id
                ),
            "payment_date":
                "2026-08-29",
            "reference_number":
                "UTR-001",
            "notes":
                "Regression payment.",
        }

        with patch.object(
            InvoiceAPIService,
            "record_payment",
            return_value={
                "invoice":
                    self.invoice,
                "payment":
                    self.payment,
            },
        ) as payment_mock:
            response = self.client.post(
                self.payment_url(),
                data=json.dumps(
                    payload
                ),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"]["payment"][
                "payment_number"
            ],
            self.payment.payment_number,
        )

        payment_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            invoice_id=str(
                self.invoice.id
            ),
            payload=payload,
        )

    def test_record_payment_validation_error(
        self,
    ):
        with patch.object(
            InvoiceAPIService,
            "record_payment",
            side_effect=(
                InvoiceAPIValidationError(
                    details={
                        "amount": [
                            (
                                "This value must be "
                                "greater than zero."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.post(
                self.payment_url(),
                data=json.dumps({
                    "amount":
                        "0.00",
                }),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_invoice_serializer_has_safe_fields(
        self,
    ):
        serialized = (
            InvoiceAPISerializer
            .serialize_detail(
                self.invoice
            )
        )

        self.assertEqual(
            serialized["id"],
            str(
                self.invoice.id
            ),
        )

        self.assertEqual(
            serialized["sales_order"]["id"],
            str(
                self.sales_order.id
            ),
        )

        self.assertEqual(
            serialized["total_amount"],
            "224.20",
        )

        self.assertEqual(
            serialized["billing"]["name"],
            self.customer.name,
        )

        self.assertNotIn(
            "organization",
            serialized,
        )

        self.assertNotIn(
            "_data",
            serialized,
        )

    def test_payment_serializer_masks_bank_account(
        self,
    ):
        serialized = (
            CustomerPaymentAPISerializer
            .serialize_detail(
                self.payment
            )
        )

        self.assertEqual(
            serialized["bank_account"][
                "masked_account_number"
            ],
            "••••7890",
        )

        self.assertNotIn(
            "account_number",
            serialized["bank_account"],
        )

    def test_service_normalizes_create_payload(
        self,
    ):
        payload = {
            "sales_order_id":
                str(
                    self.sales_order.id
                ),
            "invoice_date":
                "2026-08-29",
            "due_date":
                "2026-09-28",
            "notes":
                " Test invoice ",
        }

        with patch.object(
            SalesOrderRepository,
            "get_by_id",
            return_value=self.sales_order,
        ):
            values = (
                InvoiceAPIService
                .validate_create_payload(
                    organization=(
                        self.organization
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            values["sales_order"],
            self.sales_order,
        )

        self.assertEqual(
            values["notes"],
            "Test invoice",
        )

    def test_service_normalizes_payment_payload(
        self,
    ):
        payload = {
            "amount":
                "100.00",
            "payment_method":
                " bank_transfer ",
            "bank_account_id":
                str(
                    self.bank_account.id
                ),
            "reference_number":
                " UTR-001 ",
        }

        with patch.object(
            BankAccountRepository,
            "get_by_id",
            return_value=self.bank_account,
        ):
            values = (
                InvoiceAPIService
                .validate_payment_payload(
                    organization=(
                        self.organization
                    ),
                    payload=payload,
                )
            )

        self.assertEqual(
            values["amount"],
            Decimal("100.00"),
        )

        self.assertEqual(
            values["payment_method"],
            "BANK_TRANSFER",
        )

        self.assertEqual(
            values["bank_account"],
            self.bank_account,
        )

        self.assertEqual(
            values["reference_number"],
            "UTR-001",
        )

    def test_service_rejects_cross_tenant_bank_account(
        self,
    ):
        with patch.object(
            BankAccountRepository,
            "get_by_id",
            return_value=None,
        ):
            with self.assertRaises(
                InvoiceAPIValidationError
            ) as context:
                (
                    InvoiceAPIService
                    .validate_payment_payload(
                        organization=(
                            self.organization
                        ),
                        payload={
                            "amount":
                                "100.00",
                            "payment_method":
                                "CASH",
                            "bank_account_id":
                                str(
                                    ObjectId()
                                ),
                        },
                    )
                )

        self.assertIn(
            "bank_account_id",
            context.exception.details,
        )

    def test_invoice_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.INVOICES_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # CUSTOMER PAYMENT LIST
    # ==================================================

    def test_anonymous_payment_list_is_rejected(
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
                self.CUSTOMER_PAYMENTS_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    def test_payment_list_uses_query_pipeline(
        self,
    ):
        pipeline_result = {
            "items": [
                self.payment,
            ],
            "pagination": {
                "page": 1,
                "page_size": 25,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": None,
                "filters": {},
                "sort": [
                    "-payment_date",
                    "-created_at",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                PaymentRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ) as pipeline_mock,
        ):
            response = self.client.get(
                self.CUSTOMER_PAYMENTS_URL
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["payments"][0][
                "payment_number"
            ],
            self.payment.payment_number,
        )

        pipeline_mock.assert_called_once()

    def test_payment_list_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.CUSTOMER_PAYMENTS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_payment_list_query_error_uses_contract(
        self,
    ):
        pipeline_error = (
            APIQueryPipelineError(
                component="filtering",
                message=(
                    "Unsupported filter value."
                ),
                details={
                    "customer_id": [
                        (
                            "Enter a valid "
                            "identifier."
                        ),
                    ],
                },
            )
        )

        with (
            patch.object(
                PaymentRepository,
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
                    f"{self.CUSTOMER_PAYMENTS_URL}"
                    "?customer_id=invalid-id"
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
    # CUSTOMER PAYMENT DETAIL
    # ==================================================

    def test_customer_payment_detail(
        self,
    ):
        with patch.object(
            CustomerPaymentAPIService,
            "get_payment",
            return_value=self.payment,
        ) as get_mock:
            response = self.client.get(
                self.payment_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["payment"][
                "payment_number"
            ],
            self.payment.payment_number,
        )

        self.assertEqual(
            body["data"]["payment"][
                "allocations"
            ][0]["invoice"][
                "invoice_number"
            ],
            self.invoice.invoice_number,
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            payment_id=str(
                self.payment.id
            ),
        )

    def test_missing_payment_returns_not_found(
        self,
    ):
        with patch.object(
            CustomerPaymentAPIService,
            "get_payment",
            side_effect=LookupError(
                "Customer payment not found."
            ),
        ):
            response = self.client.get(
                self.payment_detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_malformed_payment_id_is_validation_error(
        self,
    ):
        response = self.client.get(
            (
                f"{self.CUSTOMER_PAYMENTS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_payment_serializer_has_safe_summary(
        self,
    ):
        serialized = (
            CustomerPaymentAPISerializer
            .serialize_summary(
                self.payment
            )
        )

        self.assertEqual(
            serialized["id"],
            str(
                self.payment.id
            ),
        )

        self.assertEqual(
            serialized[
                "allocation_count"
            ],
            1,
        )

        self.assertEqual(
            serialized["bank_account"][
                "masked_account_number"
            ],
            "••••7890",
        )

        self.assertNotIn(
            "organization",
            serialized,
        )

        self.assertNotIn(
            "account_number",
            serialized[
                "bank_account"
            ],
        )

    def test_service_rejects_malformed_payment_id(
        self,
    ):
        with self.assertRaises(
            CustomerPaymentAPIValidationError
        ) as context:
            (
                CustomerPaymentAPIService
                .get_payment(
                    organization=(
                        self.organization
                    ),
                    payment_id="invalid-id",
                )
            )

        self.assertIn(
            "payment_id",
            context.exception.details,
        )

    # ==================================================
    # ACCOUNTS RECEIVABLE
    # ==================================================

    def test_accounts_receivable_summary(
        self,
    ):
        now = datetime.utcnow()

        result = {
            "as_of": now,
            "invoice_count": 1,
            "overdue_invoice_count": 1,
            "customer_count": 1,
            "total_outstanding":
                Decimal("124.20"),
            "total_current":
                Decimal("0.00"),
            "total_overdue":
                Decimal("124.20"),
            "customers": [
                {
                    "customer":
                        self.customer,
                    "invoice_count": 1,
                    "overdue_invoice_count":
                        1,
                    "total_outstanding":
                        Decimal("124.20"),
                    "total_overdue":
                        Decimal("124.20"),
                },
            ],
        }

        with patch.object(
            CustomerPaymentAPIService,
            "get_receivable_summary",
            return_value=result,
        ):
            response = self.client.get(
                self.ACCOUNTS_RECEIVABLE_URL
            )

        body = self.assert_success_contract(
            response
        )

        receivable = body["data"][
            "accounts_receivable"
        ]

        self.assertEqual(
            receivable[
                "total_outstanding"
            ],
            "124.20",
        )

        self.assertEqual(
            receivable["customers"][0][
                "customer"
            ]["id"],
            str(
                self.customer.id
            ),
        )

    def test_accounts_receivable_without_permission_is_forbidden(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.ACCOUNTS_RECEIVABLE_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_receivable_aging_summary(
        self,
    ):
        now = datetime.utcnow()

        result = {
            "as_of": now,
            "invoice_count": 1,
            "total_outstanding":
                Decimal("124.20"),
            "buckets": {
                "current": {
                    "label": "Current",
                    "minimum_days": None,
                    "maximum_days": 0,
                    "invoice_count": 0,
                    "amount":
                        Decimal("0.00"),
                },
                "days_1_30": {
                    "label": "1–30 days",
                    "minimum_days": 1,
                    "maximum_days": 30,
                    "invoice_count": 1,
                    "amount":
                        Decimal("124.20"),
                },
                "days_31_60": {
                    "label": "31–60 days",
                    "minimum_days": 31,
                    "maximum_days": 60,
                    "invoice_count": 0,
                    "amount":
                        Decimal("0.00"),
                },
                "days_61_90": {
                    "label": "61–90 days",
                    "minimum_days": 61,
                    "maximum_days": 90,
                    "invoice_count": 0,
                    "amount":
                        Decimal("0.00"),
                },
                "days_over_90": {
                    "label": "Over 90 days",
                    "minimum_days": 91,
                    "maximum_days": None,
                    "invoice_count": 0,
                    "amount":
                        Decimal("0.00"),
                },
            },
            "invoices": [
                {
                    "invoice":
                        self.invoice,
                    "net_receivable":
                        Decimal("124.20"),
                    "due_date":
                        self.invoice.due_date,
                    "overdue_days": 10,
                    "is_overdue": True,
                    "bucket":
                        "days_1_30",
                },
            ],
        }

        with patch.object(
            CustomerPaymentAPIService,
            "get_aging_summary",
            return_value=result,
        ):
            response = self.client.get(
                self.RECEIVABLE_AGING_URL
            )

        body = self.assert_success_contract(
            response
        )

        aging = body["data"][
            "aging"
        ]

        self.assertEqual(
            aging["buckets"][
                "days_1_30"
            ]["amount"],
            "124.20",
        )

        self.assertEqual(
            aging["invoices"][0][
                "overdue_days"
            ],
            10,
        )

    def test_service_assigns_receivable_aging_buckets(
        self,
    ):
        as_of = datetime(
            2026,
            8,
            29,
            12,
            0,
            0,
        )

        current_invoice = (
            SimpleNamespace(
                **{
                    **vars(
                        self.invoice
                    ),
                    "id":
                        ObjectId(),
                    "due_date":
                        (
                            as_of
                            +
                            timedelta(
                                days=5
                            )
                        ),
                }
            )
        )

        overdue_invoice = (
            SimpleNamespace(
                **{
                    **vars(
                        self.invoice
                    ),
                    "id":
                        ObjectId(),
                    "due_date":
                        (
                            as_of
                            -
                            timedelta(
                                days=45
                            )
                        ),
                }
            )
        )

        with (
            patch.object(
                InvoiceRepository,
                "list_outstanding",
                return_value=[
                    current_invoice,
                    overdue_invoice,
                ],
            ),
            patch.object(
                InvoiceService,
                "get_invoice_net_receivable",
                side_effect=[
                    Decimal("50.00"),
                    Decimal("75.00"),
                ],
            ),
        ):
            result = (
                CustomerPaymentAPIService
                .get_aging_summary(
                    organization=(
                        self.organization
                    ),
                    as_of=as_of,
                )
            )

        self.assertEqual(
            result["buckets"][
                "current"
            ]["invoice_count"],
            1,
        )

        self.assertEqual(
            result["buckets"][
                "days_31_60"
            ]["invoice_count"],
            1,
        )

        self.assertEqual(
            result["total_outstanding"],
            Decimal("125.00"),
        )

    # ==================================================
    # METHOD RESTRICTIONS
    # ==================================================

    def test_payment_collection_rejects_post(
        self,
    ):
        response = self.client.post(
            self.CUSTOMER_PAYMENTS_URL,
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_receivable_summary_rejects_post(
        self,
    ):
        response = self.client.post(
            self.ACCOUNTS_RECEIVABLE_URL,
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

class SalesReturnAndCreditNoteAPIV1RegressionTestCase(
    SimpleTestCase
):

    SALES_RETURNS_URL = (
        "/api/v1/sales-returns/"
    )

    CREDIT_NOTES_URL = (
        "/api/v1/credit-notes/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Sales Return Organization",
            email="organization@example.com",
            phone="9999999999",
            address="Regression Address",
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

        self.customer = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            code="CUS-RETURN-001",
            name="Return Customer",
            email="customer@example.com",
            phone="9999999998",
            gstin="27ABCDE1234F1Z5",
            address="Customer Address",
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
            sku="RETURN-001",
            name="Return Product",
            unit="piece",
            is_active=True,
        )

        self.warehouse = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            code="WH-RETURN-001",
            name="Return Warehouse",
            address="Warehouse Address",
            city="Pune",
            state="Maharashtra",
            country="India",
            pincode="411001",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.sales_order = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            so_number="SO-RETURN-001",
            customer=self.customer,
            warehouse=self.warehouse,
            status="FULFILLED",
        )

        self.invoice = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            invoice_number="INV-RETURN-001",
            sales_order=self.sales_order,
            customer=self.customer,
            status="ISSUED",
            total_amount=Decimal("118.00"),
            amount_paid=Decimal("0.00"),
            balance_due=Decimal("118.00"),
        )

        self.return_item = SimpleNamespace(
            product=self.product,
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("18.00"),
            discount=Decimal("0.00"),
            line_subtotal=Decimal("100.00"),
            line_tax=Decimal("18.00"),
            line_total=Decimal("118.00"),
            reason="Damaged item.",
        )

        self.sales_return = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            return_number="SR-RETURN-001",
            sales_order=self.sales_order,
            invoice=self.invoice,
            customer=self.customer,
            warehouse=self.warehouse,
            status="DRAFT",
            return_date=now,
            items=[
                self.return_item,
            ],
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("118.00"),
            reason="Damaged delivery.",
            notes="Regression sales return.",
            created_by=self.user,
            confirmed_at=None,
            cancelled_at=None,
            created_at=now,
            updated_at=now,
        )

        self.credit_note_item = SimpleNamespace(
            product=self.product,
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("18.00"),
            discount=Decimal("0.00"),
            line_subtotal=Decimal("100.00"),
            line_tax=Decimal("18.00"),
            line_total=Decimal("118.00"),
        )

        self.credit_note = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            credit_note_number="CN-RETURN-001",
            invoice=self.invoice,
            sales_return=self.sales_return,
            customer=self.customer,
            status="DRAFT",
            credit_note_date=now,
            items=[
                self.credit_note_item,
            ],
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("118.00"),
            applied_amount=Decimal("0.00"),
            remaining_credit=Decimal("118.00"),
            reason="Damaged delivery.",
            notes="Regression credit note.",
            created_by=self.user,
            issued_at=None,
            cancelled_at=None,
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

    def sales_return_detail_url(self):
        return (
            f"{self.SALES_RETURNS_URL}"
            f"{self.sales_return.id}/"
        )

    def sales_return_confirm_url(self):
        return (
            f"{self.SALES_RETURNS_URL}"
            f"{self.sales_return.id}/"
            "confirm/"
        )

    def sales_return_cancel_url(self):
        return (
            f"{self.SALES_RETURNS_URL}"
            f"{self.sales_return.id}/"
            "cancel/"
        )

    def credit_note_detail_url(self):
        return (
            f"{self.CREDIT_NOTES_URL}"
            f"{self.credit_note.id}/"
        )

    def credit_note_issue_url(self):
        return (
            f"{self.CREDIT_NOTES_URL}"
            f"{self.credit_note.id}/"
            "issue/"
        )

    def credit_note_cancel_url(self):
        return (
            f"{self.CREDIT_NOTES_URL}"
            f"{self.credit_note.id}/"
            "cancel/"
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

    @staticmethod
    def pipeline_result(
        items,
        *,
        sort_field,
    ):
        return {
            "items":
                items,
            "pagination": {
                "page": 1,
                "page_size": 25,
                "total_items":
                    len(
                        items
                    ),
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "search": None,
                "filters": {},
                "sort": [
                    sort_field,
                    "id",
                ],
            },
        }

    def test_anonymous_sales_return_list_is_rejected(
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
                self.SALES_RETURNS_URL
            )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

    def test_sales_return_list_uses_query_pipeline(
        self,
    ):
        with patch.object(
            APIQueryPipelineService,
            "execute",
            return_value=(
                self.pipeline_result(
                    [
                        self.sales_return,
                    ],
                    sort_field=(
                        "-return_date"
                    ),
                )
            ),
        ) as execute_mock:
            response = self.client.get(
                self.SALES_RETURNS_URL
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            len(
                body["data"][
                    "sales_returns"
                ]
            ),
            1,
        )

        execute_mock.assert_called_once()

    def test_create_sales_return(
        self,
    ):
        with patch.object(
            SalesReturnAPIService,
            "create_sales_return",
            return_value=self.sales_return,
        ):
            response = self.client.post(
                self.SALES_RETURNS_URL,
                data=json.dumps({
                    "invoice_id":
                        str(
                            self.invoice.id
                        ),
                    "items": [
                        {
                            "product_id":
                                str(
                                    self.product.id
                                ),
                            "quantity":
                                "1.00",
                        },
                    ],
                }),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"][
                "sales_return"
            ]["return_number"],
            self.sales_return.return_number,
        )

    def test_sales_return_detail(
        self,
    ):
        with patch.object(
            SalesReturnRepository,
            "get_by_id",
            return_value=self.sales_return,
        ):
            response = self.client.get(
                self.sales_return_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "sales_return"
            ]["id"],
            str(
                self.sales_return.id
            ),
        )

    def test_malformed_sales_return_id_is_validation_error(
        self,
    ):
        response = self.client.get(
            (
                f"{self.SALES_RETURNS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_missing_sales_return_returns_not_found(
        self,
    ):
        with patch.object(
            SalesReturnRepository,
            "get_by_id",
            return_value=None,
        ):
            response = self.client.get(
                (
                    f"{self.SALES_RETURNS_URL}"
                    f"{ObjectId()}/"
                )
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_confirm_sales_return(
        self,
    ):
        confirmed = SimpleNamespace(
            **{
                **vars(
                    self.sales_return
                ),
                "status":
                    "CONFIRMED",
                "confirmed_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            SalesReturnAPIService,
            "confirm_sales_return",
            return_value=confirmed,
        ):
            response = self.client.post(
                self.sales_return_confirm_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "sales_return"
            ]["status"],
            "CONFIRMED",
        )

    def test_sales_return_state_error_is_unprocessable(
        self,
    ):
        with patch.object(
            SalesReturnAPIService,
            "confirm_sales_return",
            side_effect=(
                SalesReturnAPIStateError(
                    message=(
                        "Only draft sales returns "
                        "can be confirmed."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.sales_return_confirm_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_cancel_sales_return(
        self,
    ):
        cancelled = SimpleNamespace(
            **{
                **vars(
                    self.sales_return
                ),
                "status":
                    "CANCELLED",
                "cancelled_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            SalesReturnAPIService,
            "cancel_sales_return",
            return_value=cancelled,
        ):
            response = self.client.post(
                self.sales_return_cancel_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "sales_return"
            ]["status"],
            "CANCELLED",
        )

    def test_credit_note_list_uses_query_pipeline(
        self,
    ):
        with patch.object(
            APIQueryPipelineService,
            "execute",
            return_value=(
                self.pipeline_result(
                    [
                        self.credit_note,
                    ],
                    sort_field=(
                        "-credit_note_date"
                    ),
                )
            ),
        ):
            response = self.client.get(
                self.CREDIT_NOTES_URL
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            len(
                body["data"][
                    "credit_notes"
                ]
            ),
            1,
        )

    def test_create_credit_note(
        self,
    ):
        with patch.object(
            CreditNoteAPIService,
            "create_credit_note",
            return_value=self.credit_note,
        ):
            response = self.client.post(
                self.CREDIT_NOTES_URL,
                data=json.dumps({
                    "sales_return_id":
                        str(
                            self.sales_return.id
                        ),
                }),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"][
                "credit_note"
            ]["credit_note_number"],
            self.credit_note.credit_note_number,
        )

    def test_credit_note_detail(
        self,
    ):
        with patch.object(
            CreditNoteRepository,
            "get_by_id",
            return_value=self.credit_note,
        ):
            response = self.client.get(
                self.credit_note_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "credit_note"
            ]["id"],
            str(
                self.credit_note.id
            ),
        )

    def test_malformed_credit_note_id_is_validation_error(
        self,
    ):
        response = self.client.get(
            (
                f"{self.CREDIT_NOTES_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_missing_credit_note_returns_not_found(
        self,
    ):
        with patch.object(
            CreditNoteRepository,
            "get_by_id",
            return_value=None,
        ):
            response = self.client.get(
                (
                    f"{self.CREDIT_NOTES_URL}"
                    f"{ObjectId()}/"
                )
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_issue_credit_note(
        self,
    ):
        issued = SimpleNamespace(
            **{
                **vars(
                    self.credit_note
                ),
                "status":
                    "ISSUED",
                "applied_amount":
                    Decimal("118.00"),
                "remaining_credit":
                    Decimal("0.00"),
                "issued_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            CreditNoteAPIService,
            "issue_credit_note",
            return_value=issued,
        ):
            response = self.client.post(
                self.credit_note_issue_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "credit_note"
            ]["status"],
            "ISSUED",
        )

    def test_cancel_credit_note(
        self,
    ):
        cancelled = SimpleNamespace(
            **{
                **vars(
                    self.credit_note
                ),
                "status":
                    "CANCELLED",
                "cancelled_at":
                    datetime.utcnow(),
            }
        )

        with patch.object(
            CreditNoteAPIService,
            "cancel_credit_note",
            return_value=cancelled,
        ):
            response = self.client.post(
                self.credit_note_cancel_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "credit_note"
            ]["status"],
            "CANCELLED",
        )

    def test_credit_note_state_error_is_unprocessable(
        self,
    ):
        with patch.object(
            CreditNoteAPIService,
            "issue_credit_note",
            side_effect=(
                CreditNoteAPIStateError(
                    message=(
                        "Only draft credit notes "
                        "can be issued."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.credit_note_issue_url(),
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_collections_reject_delete(
        self,
    ):
        sales_return_response = (
            self.client.delete(
                self.SALES_RETURNS_URL
            )
        )

        credit_note_response = (
            self.client.delete(
                self.CREDIT_NOTES_URL
            )
        )

        self.assert_error_contract(
            sales_return_response,
            405,
            "METHOD_NOT_ALLOWED",
        )

        self.assert_error_contract(
            credit_note_response,
            405,
            "METHOD_NOT_ALLOWED",
        )