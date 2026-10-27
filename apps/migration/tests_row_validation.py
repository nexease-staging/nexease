from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import json

from apps.sales.repositories.customer_repository import (
    CustomerRepository,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)

from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.products.repositories.category_repository import (
    CategoryRepository,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from apps.migration.services.migration_row_validation_service import (
    MigrationRowValidationError,
    MigrationRowValidationService,
)
from apps.purchasing.repositories.supplier_repository import (
    SupplierRepository,
)
from decimal import Decimal
from types import SimpleNamespace
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)


class MigrationRowValidationServiceTestCase(
    TestCase,
):

    def setUp(self):
        self.organization = (
            SimpleNamespace(
                id="organization-1",
            )
        )

        self.category = (
            SimpleNamespace(
                id="category-1",
                name="Electronics",
                is_active=True,
            )
        )

    def _sales_order_row(
        self,
        **overrides,
    ):
        row = {
            "so_number": "MIG-SO-001",
            "customer_code": "MIG-CUST-001",
            "warehouse_code": "MIG-WH-001",
            "order_date": "2026-09-29",
            "expected_delivery_date": "2026-10-05",
            "product_sku": "MIG-PROD-001",
            "quantity": "2",
            "unit_price": "100.00",
            "tax_rate": "18.00",
            "discount": "10.00",
            "notes": "Migration sales order",
        }

        row.update(overrides)

        return row

    def _sales_invoice_row(
        self,
        **overrides,
    ):
        row = {
            "invoice_number": "MIG-INV-001",
            "sales_order_number": "MIG-SO-001",
            "invoice_date": "2026-09-29",
            "due_date": "2026-10-29",
            "notes": "Migration sales invoice",
        }

        row.update(overrides)

        return row

    def _goods_receipt_row(
        self,
        **overrides,
    ):
        row = {
            "purchase_order_number": "MIG-PO-001",
            "warehouse_code": "MIG-WH-001",
            "product_sku": "MIG-PROD-001",
            "quantity_received": "3",
            "notes": "Migration goods receipt",
        }

        row.update(overrides)

        return row

    def _goods_receipt_objects(self):
        product = SimpleNamespace(
            id="product-1",
            sku="MIG-PROD-001",
            is_active=True,
        )

        warehouse = SimpleNamespace(
            id="warehouse-1",
            code="MIG-WH-001",
            is_active=True,
        )

        po_item = SimpleNamespace(
            product=product,
            quantity=Decimal("10.00"),
            received_quantity=Decimal("2.00"),
        )

        purchase_order = SimpleNamespace(
            id="purchase-order-1",
            po_number="MIG-PO-001",
            status="CONFIRMED",
            items=[po_item],
        )

        return (
            purchase_order,
            warehouse,
            product,
        )

    def _fulfilled_sales_order(self):
        return SimpleNamespace(
            id="sales-order-1",
            so_number="MIG-SO-001",
            status="FULFILLED",
        )

    def _sales_order_objects(self):
        customer = SimpleNamespace(
            id="customer-1",
            code="MIG-CUST-001",
            is_active=True,
        )

        product = SimpleNamespace(
            id="product-1",
            sku="MIG-PROD-001",
            is_active=True,
        )

        warehouse = SimpleNamespace(
            id="warehouse-1",
            code="MIG-WH-001",
            is_active=True,
        )

        return (
            customer,
            product,
            warehouse,
        )
    # ==================================================
    # CATEGORY VALIDATION
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_by_name"
    )
    def test_valid_category_row(
        self,
        get_category_mock,
    ):
        get_category_mock.return_value = None

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "Electronics",
                        "description":
                            "Electronic products",
                    },
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            0,
        )

        self.assertTrue(
            result["can_import"]
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_by_name"
    )
    def test_category_name_required(
        self,
        get_category_mock,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "",
                    },
                ],
            )
        )

        self.assertFalse(
            result["can_import"]
        )

        self.assertEqual(
            result["rows"][0]
            ["errors"][0]["code"],
            "REQUIRED",
        )

        get_category_mock.assert_not_called()

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_by_name"
    )
    def test_duplicate_category_in_file(
        self,
        get_category_mock,
    ):
        get_category_mock.return_value = None

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "Electronics",
                    },
                    {
                        "name": "electronics",
                    },
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_by_name"
    )
    def test_existing_category_rejected(
        self,
        get_category_mock,
    ):
        get_category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "Electronics",
                    },
                ],
            )
        )

        self.assertFalse(
            result["can_import"]
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "ALREADY_EXISTS",
            codes,
        )

    def test_category_name_max_length(
        self,
    ):
        with patch(
            "apps.migration.services."
            "migration_row_validation_service."
            "CategoryRepository.get_by_name",
            return_value=None,
        ):
            result = (
                MigrationRowValidationService
                .validate_rows(
                    organization=(
                        self.organization
                    ),
                    migration_type=(
                        "CATEGORIES"
                    ),
                    rows=[
                        {
                            "name":
                                "X" * 101,
                        },
                    ],
                )
            )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "MAX_LENGTH",
            codes,
        )

    # ==================================================
    # PRODUCT VALIDATION
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_valid_product_row(
        self,
        sku_exists_mock,
        category_mock,
    ):
        sku_exists_mock.return_value = False
        category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": " item-001 ",
                        "name": "Keyboard",
                        "category": "Electronics",
                        "unit": "PCS",
                        "cost_price": "500.25",
                        "selling_price": "750.50",
                    },
                ],
            )
        )

        self.assertTrue(
            result["can_import"]
        )

        normalized = (
            result["rows"][0]
            ["normalized"]
        )

        self.assertEqual(
            normalized["sku"],
            "ITEM-001",
        )

        self.assertEqual(
            str(
                normalized["cost_price"]
            ),
            "500.25",
        )

        self.assertEqual(
            str(
                normalized["selling_price"]
            ),
            "750.50",
        )

        self.assertIs(
            normalized["category"],
            self.category,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_duplicate_sku_in_file(
        self,
        sku_exists_mock,
        category_mock,
    ):
        sku_exists_mock.return_value = False
        category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "item-001",
                        "name": "Keyboard",
                        "category": "Electronics",
                        "unit": "PCS",
                    },
                    {
                        "sku": "ITEM-001",
                        "name": "Mouse",
                        "category": "Electronics",
                        "unit": "PCS",
                    },
                ],
            )
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_existing_product_rejected(
        self,
        sku_exists_mock,
        category_mock,
    ):
        sku_exists_mock.return_value = True
        category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "ITEM-001",
                        "name": "Keyboard",
                        "category": "Electronics",
                        "unit": "PCS",
                    },
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "ALREADY_EXISTS",
            codes,
        )

        self.assertFalse(
            result["can_import"]
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_missing_category_rejected(
        self,
        sku_exists_mock,
        category_mock,
    ):
        sku_exists_mock.return_value = False
        category_mock.return_value = None

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "ITEM-001",
                        "name": "Keyboard",
                        "category": "Missing",
                        "unit": "PCS",
                    },
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "CATEGORY_NOT_FOUND",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_required_product_fields(
        self,
        sku_exists_mock,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "",
                        "name": "",
                        "category": "",
                        "unit": "",
                    },
                ],
            )
        )

        codes = {
            error["field"]
            for error
            in result["rows"][0]["errors"]
            if error["code"] == "REQUIRED"
        }

        self.assertEqual(
            codes,
            {
                "sku",
                "name",
                "category",
                "unit",
            },
        )

        sku_exists_mock.assert_not_called()

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_negative_price_rejected(
        self,
        sku_exists_mock,
        category_mock,
    ):
        sku_exists_mock.return_value = False
        category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "ITEM-001",
                        "name": "Keyboard",
                        "category": "Electronics",
                        "unit": "PCS",
                        "cost_price": "-1",
                    },
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "NEGATIVE_VALUE",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_invalid_decimal_rejected(
        self,
        sku_exists_mock,
        category_mock,
    ):
        sku_exists_mock.return_value = False
        category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "ITEM-001",
                        "name": "Keyboard",
                        "category": "Electronics",
                        "unit": "PCS",
                        "selling_price": "ABC",
                    },
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "INVALID_DECIMAL",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_price_precision_rejected(
        self,
        sku_exists_mock,
        category_mock,
    ):
        sku_exists_mock.return_value = False
        category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "ITEM-001",
                        "name": "Keyboard",
                        "category": "Electronics",
                        "unit": "PCS",
                        "selling_price": "99.999",
                    },
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "DECIMAL_PLACES",
            codes,
        )

    # ==================================================
    # CUSTOMER VALIDATION
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CustomerRepository.code_exists"
    )
    def test_valid_customer_row(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CUSTOMERS",
                rows=[
                    {
                        "code": " cust-001 ",
                        "name": " Acme India ",
                        "email":
                            " SALES@ACME.COM ",
                        "phone":
                            " +91 9876543210 ",
                        "gstin":
                            " 27abcde1234f1z5 ",
                        "billing_address":
                            " Pune Office ",
                        "shipping_address":
                            " Mumbai Warehouse ",
                        "city": " Pune ",
                        "state":
                            " Maharashtra ",
                        "country": " India ",
                        "pincode": " 411001 ",
                    },
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            0,
        )

        self.assertTrue(
            result["can_import"]
        )

        normalized = (
            result["rows"][0]
            ["normalized"]
        )

        self.assertEqual(
            normalized["code"],
            "CUST-001",
        )

        self.assertEqual(
            normalized["name"],
            "Acme India",
        )

        self.assertEqual(
            normalized["email"],
            "sales@acme.com",
        )

        self.assertEqual(
            normalized["gstin"],
            "27ABCDE1234F1Z5",
        )

        self.assertEqual(
            normalized["country"],
            "India",
        )

        self.assertEqual(
            normalized["pincode"],
            "411001",
        )

        code_exists_mock.assert_called_once_with(
            organization=self.organization,
            code="CUST-001",
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CustomerRepository.code_exists"
    )
    def test_required_customer_fields(
        self,
        code_exists_mock,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CUSTOMERS",
                rows=[
                    {
                        "code": "",
                        "name": "",
                    },
                ],
            )
        )

        required_fields = {
            error["field"]
            for error
            in result["rows"][0]["errors"]
            if error["code"] == "REQUIRED"
        }

        self.assertEqual(
            required_fields,
            {
                "code",
                "name",
            },
        )

        self.assertFalse(
            result["can_import"]
        )

        code_exists_mock.assert_not_called()

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CustomerRepository.code_exists"
    )
    def test_duplicate_customer_code_in_file(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CUSTOMERS",
                rows=[
                    {
                        "code": "cust-001",
                        "name": "Customer One",
                    },
                    {
                        "code": "CUST-001",
                        "name": "Customer Two",
                    },
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CustomerRepository.code_exists"
    )
    def test_existing_customer_rejected(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = True

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CUSTOMERS",
                rows=[
                    {
                        "code": "CUST-001",
                        "name": "Acme India",
                    },
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "ALREADY_EXISTS",
            codes,
        )

        self.assertFalse(
            result["can_import"]
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CustomerRepository.code_exists"
    )
    def test_customer_field_max_lengths(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CUSTOMERS",
                rows=[
                    {
                        "code": "X" * 51,
                        "name": "N" * 201,
                        "email": "E" * 255,
                        "phone": "1" * 31,
                        "gstin": "G" * 21,
                        "billing_address":
                            "B" * 501,
                        "shipping_address":
                            "S" * 501,
                        "city": "C" * 101,
                        "state": "S" * 101,
                        "country": "I" * 101,
                        "pincode": "P" * 21,
                    },
                ],
            )
        )

        max_length_fields = {
            error["field"]
            for error
            in result["rows"][0]["errors"]
            if error["code"] == "MAX_LENGTH"
        }

        self.assertEqual(
            max_length_fields,
            {
                "code",
                "name",
                "email",
                "phone",
                "gstin",
                "billing_address",
                "shipping_address",
                "city",
                "state",
                "country",
                "pincode",
            },
        )

        self.assertFalse(
            result["can_import"]
        )

    # ==================================================
    # SUPPLIERS
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "SupplierRepository.code_exists"
    )
    def test_valid_supplier_row_is_normalized(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SUPPLIERS",
                rows=[
                    {
                        "code": " sup-001 ",
                        "name": " ABC Supplies ",
                        "email":
                            " SALES@ABC.COM ",
                        "phone":
                            " +91 9876543210 ",
                        "gstin":
                            " 27abcde1234f1z5 ",
                        "address":
                            " Pune Office ",
                        "city": " Pune ",
                        "state":
                            " Maharashtra ",
                        "country": " India ",
                        "pincode": " 411001 ",
                    },
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )
        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            0,
        )
        self.assertTrue(
            result["can_import"]
        )

        normalized = (
            result["rows"][0]
            ["normalized"]
        )

        self.assertEqual(
            normalized["code"],
            "SUP-001",
        )
        self.assertEqual(
            normalized["name"],
            "ABC Supplies",
        )
        self.assertEqual(
            normalized["email"],
            "sales@abc.com",
        )
        self.assertEqual(
            normalized["phone"],
            "+91 9876543210",
        )
        self.assertEqual(
            normalized["gstin"],
            "27ABCDE1234F1Z5",
        )
        self.assertEqual(
            normalized["address"],
            "Pune Office",
        )
        self.assertEqual(
            normalized["city"],
            "Pune",
        )
        self.assertEqual(
            normalized["state"],
            "Maharashtra",
        )
        self.assertEqual(
            normalized["country"],
            "India",
        )
        self.assertEqual(
            normalized["pincode"],
            "411001",
        )

        code_exists_mock.assert_called_once_with(
            organization=self.organization,
            code="SUP-001",
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "SupplierRepository.code_exists"
    )
    def test_supplier_required_fields(
        self,
        code_exists_mock,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SUPPLIERS",
                rows=[
                    {
                        "code": "",
                        "name": "",
                    },
                ],
            )
        )

        required_fields = {
            error["field"]
            for error
            in result["rows"][0]["errors"]
            if error["code"] == "REQUIRED"
        }

        self.assertEqual(
            required_fields,
            {
                "code",
                "name",
            },
        )
        self.assertFalse(
            result["can_import"]
        )

        code_exists_mock.assert_not_called()

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "SupplierRepository.code_exists"
    )
    def test_duplicate_supplier_code_in_file(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SUPPLIERS",
                rows=[
                    {
                        "code": "sup-001",
                        "name": "Supplier One",
                    },
                    {
                        "code": "SUP-001",
                        "name": "Supplier Two",
                    },
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "SupplierRepository.code_exists"
    )
    def test_existing_supplier_rejected(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = True

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SUPPLIERS",
                rows=[
                    {
                        "code": "SUP-001",
                        "name": "ABC Supplies",
                    },
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "ALREADY_EXISTS",
            codes,
        )
        self.assertFalse(
            result["can_import"]
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "SupplierRepository.code_exists"
    )
    def test_supplier_field_max_lengths(
        self,
        code_exists_mock,
    ):
        code_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SUPPLIERS",
                rows=[
                    {
                        "code": "X" * 51,
                        "name": "N" * 201,
                        "email": "E" * 255,
                        "phone": "1" * 31,
                        "gstin": "G" * 21,
                        "address": "A" * 501,
                        "city": "C" * 101,
                        "state": "S" * 101,
                        "country": "I" * 101,
                        "pincode": "P" * 21,
                    },
                ],
            )
        )

        max_length_fields = {
            error["field"]
            for error
            in result["rows"][0]["errors"]
            if error["code"] == "MAX_LENGTH"
        }

        self.assertEqual(
            max_length_fields,
            {
                "code",
                "name",
                "email",
                "phone",
                "gstin",
                "address",
                "city",
                "state",
                "country",
                "pincode",
            },
        )

        self.assertFalse(
            result["can_import"]
        )

    # ==================================================
    # WAREHOUSES
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.name_exists"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.code_exists"
    )
    def test_valid_warehouse_row_is_normalized(
        self,
        code_exists_mock,
        name_exists_mock,
    ):
        code_exists_mock.return_value = False
        name_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="WAREHOUSES",
                rows=[
                    {
                        "code": " wh-001 ",
                        "name": " Main Warehouse ",
                        "address": " Pune Office ",
                        "city": " Pune ",
                        "state": " Maharashtra ",
                        "country": " India ",
                        "pincode": " 411001 ",
                    },
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )
        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            0,
        )
        self.assertTrue(
            result["can_import"]
        )

        normalized = (
            result["rows"][0]
            ["normalized"]
        )

        self.assertEqual(
            normalized["code"],
            "WH-001",
        )
        self.assertEqual(
            normalized["name"],
            "Main Warehouse",
        )
        self.assertEqual(
            normalized["address"],
            "Pune Office",
        )
        self.assertEqual(
            normalized["city"],
            "Pune",
        )
        self.assertEqual(
            normalized["state"],
            "Maharashtra",
        )
        self.assertEqual(
            normalized["country"],
            "India",
        )
        self.assertEqual(
            normalized["pincode"],
            "411001",
        )

        code_exists_mock.assert_called_once_with(
            organization=self.organization,
            code="WH-001",
        )

        name_exists_mock.assert_called_once_with(
            organization=self.organization,
            name="Main Warehouse",
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.name_exists"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.code_exists"
    )
    def test_warehouse_required_fields(
        self,
        code_exists_mock,
        name_exists_mock,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="WAREHOUSES",
                rows=[
                    {
                        "code": "",
                        "name": "",
                    },
                ],
            )
        )

        required_fields = {
            error["field"]
            for error
            in result["rows"][0]["errors"]
            if error["code"] == "REQUIRED"
        }

        self.assertEqual(
            required_fields,
            {
                "code",
                "name",
            },
        )

        self.assertFalse(
            result["can_import"]
        )

        code_exists_mock.assert_not_called()
        name_exists_mock.assert_not_called()

    # ==================================================
    # CONTRACT
    # ==================================================

    def test_empty_rows_cannot_import(
        self,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[],
            )
        )

        self.assertEqual(
            result["total_rows"],
            0,
        )

        self.assertFalse(
            result["can_import"]
        )

    def test_unsupported_type_rejected(
        self,
    ):
        with self.assertRaises(
            MigrationRowValidationError
        ):
            (
                MigrationRowValidationService
                .validate_rows(
                    organization=(
                        self.organization
                    ),
                    migration_type=(
                        "VENDORS"
                    ),
                    rows=[],
                )
            )

    def test_invalid_row_structure(
        self,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    "not-a-dictionary",
                ],
            )
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        self.assertEqual(
            result["rows"][0]
            ["errors"][0]["code"],
            "INVALID_ROW",
        )

        self.assertIsNone(
            result["rows"][0]
            ["normalized"]
        )

    @patch(
        "apps.products.models."
        "Product.save"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_active_by_name"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.sku_exists"
    )
    def test_product_dry_run_never_saves_product(
        self,
        sku_exists_mock,
        category_mock,
        product_save_mock,
    ):
        sku_exists_mock.return_value = False
        category_mock.return_value = (
            self.category
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="PRODUCTS",
                rows=[
                    {
                        "sku": "ITEM-001",
                        "name": "Keyboard",
                        "category": "Electronics",
                        "unit": "PCS",
                        "cost_price": "500.00",
                        "selling_price": "750.00",
                    },
                ],
            )
        )

        self.assertTrue(
            result["can_import"]
        )

        product_save_mock.assert_not_called()



    @patch(
        "apps.products.models."
        "Category.save"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "CategoryRepository.get_by_name"
    )
    def test_category_dry_run_never_saves_category(
        self,
        get_category_mock,
        category_save_mock,
    ):
        get_category_mock.return_value = None

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "Electronics",
                        "description":
                            "Electronic products",
                    },
                ],
            )
        )

        self.assertTrue(
            result["can_import"]
        )

        category_save_mock.assert_not_called()

    @patch.object(
        CategoryRepository,
        "get_by_name",
    )
    def test_existing_category_is_skipped_when_enabled(
        self,
        get_by_name_mock,
    ):
        get_by_name_mock.return_value = (
            SimpleNamespace(
                id="existing-category",
                name="Electronics",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=(
                    self.organization
                ),
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "Electronics",
                        "description":
                            "Existing category",
                    },
                ],
                skip_duplicates=True,
            )
        )

        row = result["rows"][0]

        self.assertTrue(
            row["valid"]
        )

        self.assertTrue(
            row["skipped"]
        )

        self.assertEqual(
            {
                error["code"]
                for error in row["errors"]
            },
            {"ALREADY_EXISTS"},
        )


    @patch.object(
        CategoryRepository,
        "get_by_name",
    )
    def test_existing_category_remains_invalid_when_skip_disabled(
        self,
        get_by_name_mock,
    ):
        get_by_name_mock.return_value = (
            SimpleNamespace(
                id="existing-category",
                name="Electronics",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=(
                    self.organization
                ),
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "Electronics",
                    },
                ],
                skip_duplicates=False,
            )
        )

        row = result["rows"][0]

        self.assertFalse(
            row["valid"]
        )

        self.assertFalse(
            row["skipped"]
        )

        self.assertIn(
            "ALREADY_EXISTS",
            {
                error["code"]
                for error in row["errors"]
            },
        )

    @patch.object(
        CategoryRepository,
        "get_by_name",
        return_value=None,
    )
    def test_in_file_duplicate_is_not_skipped(
        self,
        get_by_name_mock,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=(
                    self.organization
                ),
                migration_type="CATEGORIES",
                rows=[
                    {
                        "name": "Electronics",
                    },
                    {
                        "name": "Electronics",
                    },
                ],
                skip_duplicates=True,
            )
        )

        duplicate_row = result["rows"][1]

        self.assertFalse(
            duplicate_row["valid"]
        )

        self.assertFalse(
            duplicate_row["skipped"]
        )

        self.assertIn(
            "DUPLICATE_IN_FILE",
            {
                error["code"]
                for error
                in duplicate_row["errors"]
            },
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.name_exists"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.code_exists"
    )
    def test_duplicate_warehouse_code_in_file(
        self,
        code_exists_mock,
        name_exists_mock,
    ):
        code_exists_mock.return_value = False
        name_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="WAREHOUSES",
                rows=[
                    {
                        "code": "wh-001",
                        "name": "Main Warehouse",
                    },
                    {
                        "code": "WH-001",
                        "name": "Secondary Warehouse",
                    },
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.name_exists"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.code_exists"
    )
    def test_duplicate_warehouse_name_in_file(
        self,
        code_exists_mock,
        name_exists_mock,
    ):
        code_exists_mock.return_value = False
        name_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="WAREHOUSES",
                rows=[
                    {
                        "code": "WH-001",
                        "name": "Main Warehouse",
                    },
                    {
                        "code": "WH-002",
                        "name": "main warehouse",
                    },
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        errors = (
            result["rows"][1]
            ["errors"]
        )

        self.assertTrue(
            any(
                error["field"] == "name"
                and error["code"]
                == "DUPLICATE_IN_FILE"
                for error in errors
            )
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.name_exists"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.code_exists"
    )
    def test_existing_warehouse_code_rejected(
        self,
        code_exists_mock,
        name_exists_mock,
    ):
        code_exists_mock.return_value = True
        name_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="WAREHOUSES",
                rows=[
                    {
                        "code": "WH-001",
                        "name": "Main Warehouse",
                    },
                ],
            )
        )

        errors = (
            result["rows"][0]
            ["errors"]
        )

        self.assertTrue(
            any(
                error["field"] == "code"
                and error["code"]
                == "ALREADY_EXISTS"
                for error in errors
            )
        )

        self.assertFalse(
            result["can_import"]
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.name_exists"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.code_exists"
    )
    def test_existing_warehouse_name_rejected(
        self,
        code_exists_mock,
        name_exists_mock,
    ):
        code_exists_mock.return_value = False
        name_exists_mock.return_value = True

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="WAREHOUSES",
                rows=[
                    {
                        "code": "WH-001",
                        "name": "Main Warehouse",
                    },
                ],
            )
        )

        errors = (
            result["rows"][0]
            ["errors"]
        )

        self.assertTrue(
            any(
                error["field"] == "name"
                and error["code"]
                == "ALREADY_EXISTS"
                for error in errors
            )
        )

        self.assertFalse(
            result["can_import"]
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.name_exists"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.code_exists"
    )
    def test_warehouse_field_max_lengths(
        self,
        code_exists_mock,
        name_exists_mock,
    ):
        code_exists_mock.return_value = False
        name_exists_mock.return_value = False

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="WAREHOUSES",
                rows=[
                    {
                        "code": "X" * 51,
                        "name": "N" * 201,
                        "address": "A" * 501,
                        "city": "C" * 101,
                        "state": "S" * 101,
                        "country": "I" * 101,
                        "pincode": "P" * 21,
                    },
                ],
            )
        )

        max_length_fields = {
            error["field"]
            for error
            in result["rows"][0]["errors"]
            if error["code"] == "MAX_LENGTH"
        }

        self.assertEqual(
            max_length_fields,
            {
                "code",
                "name",
                "address",
                "city",
                "state",
                "country",
                "pincode",
            },
        )

        self.assertFalse(
            result["can_import"]
        )


    # ==================================================
    # INVENTORY
    # ==================================================

    @patch.object(
        InventoryRepository,
        "exists_for_product_and_warehouse",
        return_value=False,
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.get_by_code"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.get_by_sku"
    )
    def test_valid_inventory_row_is_normalized(
        self,
        get_product_mock,
        get_warehouse_mock,
        inventory_exists_mock,
    ):
        product = SimpleNamespace(
            id="product-1",
            sku="SKU-001",
        )

        warehouse = SimpleNamespace(
            id="warehouse-1",
            code="WH-001",
        )

        get_product_mock.return_value = product
        get_warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="INVENTORY",
                rows=[
                    {
                        "product_sku": " sku-001 ",
                        "warehouse_code": " wh-001 ",
                        "quantity": "25.50",
                    },
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )
        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            0,
        )
        self.assertTrue(
            result["can_import"]
        )

        normalized = (
            result["rows"][0]["normalized"]
        )

        self.assertEqual(
            normalized["product_sku"],
            "SKU-001",
        )
        self.assertIs(
            normalized["product"],
            product,
        )
        self.assertEqual(
            normalized["warehouse_code"],
            "WH-001",
        )
        self.assertIs(
            normalized["warehouse"],
            warehouse,
        )
        self.assertEqual(
            normalized["quantity"],
            Decimal("25.50"),
        )

        get_product_mock.assert_called_once_with(
            organization=self.organization,
            sku="SKU-001",
        )
        get_warehouse_mock.assert_called_once_with(
            organization=self.organization,
            code="WH-001",
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.get_by_code"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.get_by_sku"
    )
    def test_inventory_missing_product_is_rejected(
        self,
        get_product_mock,
        get_warehouse_mock,
    ):
        get_product_mock.return_value = None
        get_warehouse_mock.return_value = (
            SimpleNamespace(
                id="warehouse-1",
                code="WH-001",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="INVENTORY",
                rows=[
                    {
                        "product_sku": "SKU-404",
                        "warehouse_code": "WH-001",
                        "quantity": "10.00",
                    },
                ],
            )
        )

        errors = result["rows"][0]["errors"]

        self.assertTrue(
            any(
                error["field"] == "product_sku"
                and error["code"]
                == "PRODUCT_NOT_FOUND"
                for error in errors
            )
        )
        self.assertFalse(
            result["can_import"]
        )

    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.get_by_code"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.get_by_sku"
    )
    def test_inventory_missing_warehouse_is_rejected(
        self,
        get_product_mock,
        get_warehouse_mock,
    ):
        get_product_mock.return_value = (
            SimpleNamespace(
                id="product-1",
                sku="SKU-001",
            )
        )
        get_warehouse_mock.return_value = None

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="INVENTORY",
                rows=[
                    {
                        "product_sku": "SKU-001",
                        "warehouse_code": "WH-404",
                        "quantity": "10.00",
                    },
                ],
            )
        )

        errors = result["rows"][0]["errors"]

        self.assertTrue(
            any(
                error["field"]
                == "warehouse_code"
                and error["code"]
                == "WAREHOUSE_NOT_FOUND"
                for error in errors
            )
        )
        self.assertFalse(
            result["can_import"]
        )

    @patch.object(
        InventoryRepository,
        "exists_for_product_and_warehouse",
        return_value=False,
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.get_by_code"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.get_by_sku"
    )
    def test_inventory_invalid_quantities_are_rejected(
        self,
        get_product_mock,
        get_warehouse_mock,
        inventory_exists_mock,
    ):
        get_product_mock.return_value = (
            SimpleNamespace(
                id="product-1",
                sku="SKU-001",
            )
        )
        get_warehouse_mock.return_value = (
            SimpleNamespace(
                id="warehouse-1",
                code="WH-001",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="INVENTORY",
                rows=[
                    {
                        "product_sku": "SKU-001",
                        "warehouse_code": "WH-001",
                        "quantity": "abc",
                    },
                    {
                        "product_sku": "SKU-002",
                        "warehouse_code": "WH-002",
                        "quantity": "-5",
                    },
                ],
            )
        )

        self.assertEqual(
            result["invalid_rows"],
            2,
        )
        self.assertFalse(
            result["can_import"]
        )

        for row in result["rows"]:
            self.assertTrue(
                any(
                    error["field"] == "quantity"
                    for error in row["errors"]
                )
            )

    @patch.object(
        InventoryRepository,
        "exists_for_product_and_warehouse",
        return_value=False,
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.get_by_code"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.get_by_sku"
    )
    def test_duplicate_inventory_combination_in_file(
        self,
        get_product_mock,
        get_warehouse_mock,
        inventory_exists_mock,
    ):
        get_product_mock.return_value = (
            SimpleNamespace(
                id="product-1",
                sku="SKU-001",
            )
        )
        get_warehouse_mock.return_value = (
            SimpleNamespace(
                id="warehouse-1",
                code="WH-001",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="INVENTORY",
                rows=[
                    {
                        "product_sku": "sku-001",
                        "warehouse_code": "wh-001",
                        "quantity": "10",
                    },
                    {
                        "product_sku": "SKU-001",
                        "warehouse_code": "WH-001",
                        "quantity": "20",
                    },
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        errors = result["rows"][1]["errors"]

        self.assertTrue(
            any(
                error["code"]
                == "DUPLICATE_IN_FILE"
                for error in errors
            )
        )

        self.assertFalse(
            result["can_import"]
        )

    @patch.object(
        InventoryRepository,
        "exists_for_product_and_warehouse",
        return_value=True,
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.get_by_code"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.get_by_sku"
    )
    def test_existing_inventory_is_rejected(
        self,
        get_product_mock,
        get_warehouse_mock,
        inventory_exists_mock,
    ):
        product = SimpleNamespace(
            id="product-1",
            sku="SKU-001",
        )
        warehouse = SimpleNamespace(
            id="warehouse-1",
            code="WH-001",
        )

        get_product_mock.return_value = product
        get_warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="INVENTORY",
                rows=[
                    {
                        "product_sku": "SKU-001",
                        "warehouse_code": "WH-001",
                        "quantity": "25.00",
                    },
                ],
                skip_duplicates=False,
            )
        )

        row = result["rows"][0]

        self.assertFalse(row["valid"])
        self.assertFalse(row["skipped"])

        self.assertIn(
            "ALREADY_EXISTS",
            {
                error["code"]
                for error in row["errors"]
            },
        )

        self.assertFalse(
            result["can_import"]
        )

        inventory_exists_mock.assert_called_once_with(
            organization=self.organization,
            product=product,
            warehouse=warehouse,
        )

    @patch.object(
        InventoryRepository,
        "exists_for_product_and_warehouse",
        return_value=True,
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "WarehouseRepository.get_by_code"
    )
    @patch(
        "apps.migration.services."
        "migration_row_validation_service."
        "ProductRepository.get_by_sku"
    )
    def test_existing_inventory_can_be_skipped(
        self,
        get_product_mock,
        get_warehouse_mock,
        inventory_exists_mock,
    ):
        get_product_mock.return_value = (
            SimpleNamespace(
                id="product-1",
                sku="SKU-001",
            )
        )
        get_warehouse_mock.return_value = (
            SimpleNamespace(
                id="warehouse-1",
                code="WH-001",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="INVENTORY",
                rows=[
                    {
                        "product_sku": "SKU-001",
                        "warehouse_code": "WH-001",
                        "quantity": "25.00",
                    },
                ],
                skip_duplicates=True,
            )
        )

        row = result["rows"][0]

        self.assertTrue(row["valid"])
        self.assertTrue(row["skipped"])

        self.assertEqual(
            {
                error["code"]
                for error in row["errors"]
            },
            {"ALREADY_EXISTS"},
        )

        self.assertTrue(
            result["can_import"]
        )

    # ==================================================
    # SALES ORDER VALIDATION
    # ==================================================

    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_row_valid(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product,
            warehouse,
        ) = self._sales_order_objects()

        customer_mock.return_value = customer
        product_mock.return_value = product
        warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row()
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            0,
        )

        self.assertTrue(
            result["can_import"]
        )

        normalized = (
            result["rows"][0]["normalized"]
        )

        self.assertEqual(
            normalized["so_number"],
            "MIG-SO-001",
        )

        self.assertEqual(
            normalized["customer_id"],
            "customer-1",
        )

        self.assertEqual(
            normalized["product_id"],
            "product-1",
        )

        self.assertEqual(
            normalized["warehouse_id"],
            "warehouse-1",
        )

        self.assertEqual(
            normalized["order_date"],
            "2026-09-29",
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_allows_multiple_products(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product_one,
            warehouse,
        ) = self._sales_order_objects()

        product_two = SimpleNamespace(
            id="product-2",
            sku="MIG-PROD-002",
            is_active=True,
        )

        customer_mock.return_value = customer

        product_mock.side_effect = (
            product_one,
            product_two,
        )

        warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row(
                        product_sku="MIG-PROD-001",
                    ),
                    self._sales_order_row(
                        product_sku="MIG-PROD-002",
                    ),
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            2,
        )

        self.assertEqual(
            result["valid_rows"],
            2,
        )

        self.assertEqual(
            result["invalid_rows"],
            0,
        )

        self.assertTrue(
            result["can_import"]
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_duplicate_product_is_invalid(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product,
            warehouse,
        ) = self._sales_order_objects()

        customer_mock.return_value = customer
        product_mock.return_value = product
        warehouse_mock.return_value = warehouse

        row = self._sales_order_row()

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    row,
                    dict(row),
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        errors = result["rows"][1]["errors"]

        self.assertIn(
            "DUPLICATE_IN_FILE",
            {
                error["code"]
                for error in errors
            },
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
        return_value=None,
    )
    def test_sales_order_missing_customer_is_invalid(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        product_mock.return_value = SimpleNamespace(
            id="product-1",
            is_active=True,
        )

        warehouse_mock.return_value = SimpleNamespace(
            id="warehouse-1",
            is_active=True,
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "CUSTOMER_NOT_FOUND",
            codes,
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
        return_value=None,
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_missing_product_is_invalid(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        customer_mock.return_value = SimpleNamespace(
            id="customer-1",
            is_active=True,
        )

        warehouse_mock.return_value = SimpleNamespace(
            id="warehouse-1",
            is_active=True,
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "PRODUCT_NOT_FOUND",
            codes,
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
        return_value=None,
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_missing_warehouse_is_invalid(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        customer_mock.return_value = SimpleNamespace(
            id="customer-1",
            is_active=True,
        )

        product_mock.return_value = SimpleNamespace(
            id="product-1",
            is_active=True,
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "WAREHOUSE_NOT_FOUND",
            codes,
        )

    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_existing_number_is_invalid(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product,
            warehouse,
        ) = self._sales_order_objects()

        customer_mock.return_value = customer
        product_mock.return_value = product
        warehouse_mock.return_value = warehouse

        sales_order_mock.return_value = (
            SimpleNamespace(
                id="existing-so",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "ALREADY_EXISTS",
            codes,
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_invalid_quantity(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product,
            warehouse,
        ) = self._sales_order_objects()

        customer_mock.return_value = customer
        product_mock.return_value = product
        warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row(
                        quantity="0",
                    )
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "INVALID_QUANTITY",
            codes,
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_delivery_before_order_date(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product,
            warehouse,
        ) = self._sales_order_objects()

        customer_mock.return_value = customer
        product_mock.return_value = product
        warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row(
                        order_date="2026-09-29",
                        expected_delivery_date=(
                            "2026-09-20"
                        ),
                    )
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "INVALID_DELIVERY_DATE",
            codes,
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_discount_exceeds_subtotal(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product,
            warehouse,
        ) = self._sales_order_objects()

        customer_mock.return_value = customer
        product_mock.return_value = product
        warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row(
                        quantity="2",
                        unit_price="100",
                        discount="250",
                    )
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "INVALID_DISCOUNT",
            codes,
        )

    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        CustomerRepository,
        "get_by_code",
    )
    def test_sales_order_normalized_result_is_json_safe(
        self,
        customer_mock,
        product_mock,
        warehouse_mock,
        sales_order_mock,
    ):
        (
            customer,
            product,
            warehouse,
        ) = self._sales_order_objects()

        customer_mock.return_value = customer
        product_mock.return_value = product
        warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_ORDERS",
                rows=[
                    self._sales_order_row()
                ],
            )
        )

        normalized = (
            result["rows"][0]["normalized"]
        )

        serialized = json.dumps(
            normalized
        )

        self.assertIsInstance(
            serialized,
            str,
        )

        self.assertEqual(
            normalized["customer_id"],
            "customer-1",
        )

        self.assertEqual(
            normalized["product_id"],
            "product-1",
        )

        self.assertEqual(
            normalized["warehouse_id"],
            "warehouse-1",
        )

    @patch.object(
        InvoiceRepository,
        "get_by_sales_order",
        return_value=None,
    )
    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
        return_value=None,
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    def test_sales_invoice_valid_row(
        self,
        sales_order_mock,
        invoice_number_mock,
        sales_order_invoice_mock,
    ):
        sales_order_mock.return_value = (
            self._fulfilled_sales_order()
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row()
                ],
            )
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            0,
        )

        self.assertTrue(
            result["can_import"]
        )

        self.assertEqual(
            result["rows"][0]["errors"],
            [],
        )


    @patch.object(
        InvoiceRepository,
        "get_by_sales_order",
        return_value=None,
    )
    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
        return_value=None,
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    def test_sales_invoice_draft_sales_order_is_invalid(
        self,
        sales_order_mock,
        invoice_number_mock,
        sales_order_invoice_mock,
    ):
        sales_order_mock.return_value = (
            SimpleNamespace(
                id="sales-order-1",
                so_number="MIG-SO-001",
                status="DRAFT",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertEqual(
            result["valid_rows"],
            0,
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        self.assertIn(
            "INVALID_STATUS",
            codes,
        )


    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
        return_value=None,
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
        return_value=None,
    )
    def test_sales_invoice_missing_sales_order_is_invalid(
        self,
        sales_order_mock,
        invoice_number_mock,
    ):
        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertEqual(
            result["valid_rows"],
            0,
        )

        self.assertIn(
            "NOT_FOUND",
            codes,
        )


    @patch.object(
        InvoiceRepository,
        "get_by_sales_order",
        return_value=None,
    )
    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    def test_sales_invoice_existing_number_is_invalid(
        self,
        sales_order_mock,
        invoice_number_mock,
        sales_order_invoice_mock,
    ):
        sales_order_mock.return_value = (
            self._fulfilled_sales_order()
        )

        invoice_number_mock.return_value = (
            SimpleNamespace(
                id="invoice-existing",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertEqual(
            result["valid_rows"],
            0,
        )

        self.assertIn(
            "ALREADY_EXISTS",
            codes,
        )

    @patch.object(
        InvoiceRepository,
        "get_by_sales_order",
    )
    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
        return_value=None,
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    def test_sales_invoice_sales_order_already_invoiced_is_invalid(
        self,
        sales_order_mock,
        invoice_number_mock,
        sales_order_invoice_mock,
    ):
        sales_order = self._fulfilled_sales_order()

        sales_order_mock.return_value = sales_order

        sales_order_invoice_mock.return_value = (
            SimpleNamespace(
                id="existing-invoice",
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertEqual(
            result["valid_rows"],
            0,
        )

        self.assertIn(
            "ALREADY_EXISTS",
            codes,
        )


    @patch.object(
        InvoiceRepository,
        "get_by_sales_order",
        return_value=None,
    )
    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
        return_value=None,
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    def test_sales_invoice_duplicate_number_in_file_is_invalid(
        self,
        sales_order_mock,
        invoice_number_mock,
        sales_order_invoice_mock,
    ):
        sales_order_one = SimpleNamespace(
            id="sales-order-1",
            so_number="MIG-SO-001",
            status="FULFILLED",
        )

        sales_order_two = SimpleNamespace(
            id="sales-order-2",
            so_number="MIG-SO-002",
            status="FULFILLED",
        )

        sales_order_mock.side_effect = (
            sales_order_one,
            sales_order_two,
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row(
                        invoice_number="MIG-INV-001",
                        sales_order_number="MIG-SO-001",
                    ),
                    self._sales_invoice_row(
                        invoice_number="MIG-INV-001",
                        sales_order_number="MIG-SO-002",
                    ),
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )


    @patch.object(
        InvoiceRepository,
        "get_by_sales_order",
        return_value=None,
    )
    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
        return_value=None,
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    def test_sales_invoice_duplicate_sales_order_in_file_is_invalid(
        self,
        sales_order_mock,
        invoice_number_mock,
        sales_order_invoice_mock,
    ):
        sales_order = (
            self._fulfilled_sales_order()
        )

        sales_order_mock.return_value = (
            sales_order
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row(
                        invoice_number="MIG-INV-001",
                    ),
                    self._sales_invoice_row(
                        invoice_number="MIG-INV-002",
                    ),
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )

        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )


    @patch.object(
        InvoiceRepository,
        "get_by_sales_order",
        return_value=None,
    )
    @patch.object(
        InvoiceRepository,
        "get_by_invoice_number",
        return_value=None,
    )
    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    def test_sales_invoice_due_date_before_invoice_date_is_invalid(
        self,
        sales_order_mock,
        invoice_number_mock,
        sales_order_invoice_mock,
    ):
        sales_order_mock.return_value = (
            self._fulfilled_sales_order()
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="SALES_INVOICES",
                rows=[
                    self._sales_invoice_row(
                        invoice_date="2026-09-29",
                        due_date="2026-09-20",
                    )
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertEqual(
            result["valid_rows"],
            0,
        )

        self.assertIn(
            "INVALID_DATE_RANGE",
            codes,
        )

    # ==================================================
    # GOODS RECEIPT VALIDATION
    # ==================================================

    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
    )
    def test_valid_goods_receipt_row(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        (
            purchase_order,
            warehouse,
            product,
        ) = self._goods_receipt_objects()

        purchase_order_mock.return_value = (
            purchase_order
        )
        warehouse_mock.return_value = warehouse
        product_mock.return_value = product

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row()
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            0,
        )
        self.assertTrue(
            result["can_import"]
        )

        normalized = (
            result["rows"][0]["normalized"]
        )

        self.assertEqual(
            normalized[
                "purchase_order_number"
            ],
            "MIG-PO-001",
        )
        self.assertEqual(
            normalized["warehouse_code"],
            "MIG-WH-001",
        )
        self.assertEqual(
            normalized["product_sku"],
            "MIG-PROD-001",
        )
        self.assertEqual(
            normalized[
                "quantity_received"
            ],
            "3.00",
        )


    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
    )
    def test_goods_receipt_exceeds_remaining_is_invalid(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        (
            purchase_order,
            warehouse,
            product,
        ) = self._goods_receipt_objects()

        purchase_order_mock.return_value = (
            purchase_order
        )
        warehouse_mock.return_value = warehouse
        product_mock.return_value = product

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row(
                        quantity_received="9",
                    )
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            0,
        )
        self.assertEqual(
            result["invalid_rows"],
            1,
        )
        self.assertFalse(
            result["can_import"]
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "EXCEEDS_REMAINING",
            codes,
        )


    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
    )
    def test_goods_receipt_duplicate_line_is_invalid(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        (
            purchase_order,
            warehouse,
            product,
        ) = self._goods_receipt_objects()

        purchase_order_mock.return_value = (
            purchase_order
        )
        warehouse_mock.return_value = warehouse
        product_mock.return_value = product

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row(
                        quantity_received="3",
                    ),
                    self._goods_receipt_row(
                        quantity_received="2",
                    ),
                ],
            )
        )

        self.assertEqual(
            result["valid_rows"],
            1,
        )
        self.assertEqual(
            result["invalid_rows"],
            1,
        )

        codes = {
            error["code"]
            for error
            in result["rows"][1]["errors"]
        }

        self.assertIn(
            "DUPLICATE_IN_FILE",
            codes,
        )


    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
        return_value=None,
    )
    def test_goods_receipt_purchase_order_not_found(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        warehouse_mock.return_value = (
            SimpleNamespace(
                id="warehouse-1",
                code="MIG-WH-001",
                is_active=True,
            )
        )

        product_mock.return_value = (
            SimpleNamespace(
                id="product-1",
                sku="MIG-PROD-001",
                is_active=True,
            )
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "PO_NOT_FOUND",
            codes,
        )


    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
    )
    def test_goods_receipt_invalid_po_status(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        (
            purchase_order,
            warehouse,
            product,
        ) = self._goods_receipt_objects()

        purchase_order.status = "DRAFT"

        purchase_order_mock.return_value = (
            purchase_order
        )
        warehouse_mock.return_value = warehouse
        product_mock.return_value = product

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "INVALID_STATUS",
            codes,
        )


    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
        return_value=None,
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
    )
    def test_goods_receipt_warehouse_not_found(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        (
            purchase_order,
            _,
            product,
        ) = self._goods_receipt_objects()

        purchase_order_mock.return_value = (
            purchase_order
        )
        product_mock.return_value = product

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "WAREHOUSE_NOT_FOUND",
            codes,
        )


    @patch.object(
        ProductRepository,
        "get_by_sku",
        return_value=None,
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
    )
    def test_goods_receipt_product_not_found(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        (
            purchase_order,
            warehouse,
            _,
        ) = self._goods_receipt_objects()

        purchase_order_mock.return_value = (
            purchase_order
        )
        warehouse_mock.return_value = warehouse

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row()
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "PRODUCT_NOT_FOUND",
            codes,
        )


    @patch.object(
        ProductRepository,
        "get_by_sku",
    )
    @patch.object(
        WarehouseRepository,
        "get_by_code",
    )
    @patch.object(
        PurchaseOrderRepository,
        "get_by_po_number",
    )
    def test_goods_receipt_product_not_on_po(
        self,
        purchase_order_mock,
        warehouse_mock,
        product_mock,
    ):
        (
            purchase_order,
            warehouse,
            _,
        ) = self._goods_receipt_objects()

        different_product = SimpleNamespace(
            id="product-2",
            sku="MIG-PROD-002",
            is_active=True,
        )

        purchase_order_mock.return_value = (
            purchase_order
        )
        warehouse_mock.return_value = warehouse
        product_mock.return_value = (
            different_product
        )

        result = (
            MigrationRowValidationService
            .validate_rows(
                organization=self.organization,
                migration_type="GOODS_RECEIPTS",
                rows=[
                    self._goods_receipt_row(
                        product_sku="MIG-PROD-002",
                    )
                ],
            )
        )

        codes = {
            error["code"]
            for error
            in result["rows"][0]["errors"]
        }

        self.assertIn(
            "PRODUCT_NOT_ON_PO",
            codes,
        )