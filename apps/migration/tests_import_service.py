from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime
from django.test import SimpleTestCase

from apps.migration.services.migration_import_service import (
    MigrationImportError,
    MigrationImportService,
)
from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)
from apps.products.services.category_api_service import (
    CategoryAPIService,
)
from apps.products.services.product_api_service import (
    ProductAPIService,
)
from apps.inventory.services.inventory_api_service import (
    InventoryAPIService,
)
from apps.sales.repositories.customer_repository import (
    CustomerRepository,
)
from apps.purchasing.repositories.supplier_repository import (
    SupplierRepository,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from apps.purchasing.services.purchase_order_service import (
    PurchaseOrderService,
)
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.services.sales_order_service import (
    SalesOrderService,
)
from apps.sales.services.invoice_service import (
    InvoiceService,
)
from apps.purchasing.services.goods_receipt_service import (
    GoodsReceiptService,
)


class MigrationImportServiceTestCase(
    SimpleTestCase
):

    def setUp(self):
        self.organization = SimpleNamespace(
            id="organization-1",
        )

        self.other_organization = (
            SimpleNamespace(
                id="organization-2",
            )
        )

        self.category = SimpleNamespace(
            id="category-1",
        )

        self.user = SimpleNamespace(
            id="user-1",
        )

    def make_batch(
        self,
        *,
        migration_type="PRODUCTS",
        can_import=True,
        rows=None,
        organization=None,
        options=None,
        created_by=None,
    ):
        if rows is None:
            rows = [
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "sku": "SKU-001",
                        "name": "Test Product",
                        "description": "",
                        "category":
                            self.category,
                        "category_name":
                            "Electronics",
                        "brand": "Test Brand",
                        "unit": "PCS",
                        "cost_price": "100.00",
                        "selling_price":
                            "150.00",
                        "barcode": "",
                    },
                },
            ]

        return SimpleNamespace(
            id="batch-1",
            created_by=(
                created_by
                or
                self.user
            ),
            organization=(
                organization
                or
                self.organization
            ),
            migration_type=(
                migration_type
            ),
            status="VALIDATED",
            valid_rows=len(rows),
            invalid_rows=0,
            options=options or {},
            validation_result={
                "migration_type":
                    migration_type,
                "total_rows": len(rows),
                "valid_rows": len(rows),
                "invalid_rows": 0,
                "can_import":
                    can_import,
                "rows":
                    rows,
            },
        )

    # ==================================================
    # BASIC VALIDATION
    # ==================================================

    def test_import_requires_organization(
        self,
    ):
        batch = self.make_batch()

        with self.assertRaises(
            MigrationImportError
        ):
            (
                MigrationImportService
                .import_batch(
                    organization=None,
                    batch=batch,
                )
            )

    def test_import_requires_batch(
        self,
    ):
        with self.assertRaises(
            MigrationImportError
        ):
            (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=None,
                )
            )

    def test_import_rejects_cross_tenant_batch(
        self,
    ):
        batch = self.make_batch(
            organization=(
                self.other_organization
            ),
        )

        with self.assertRaises(
            MigrationImportError
        ):
            (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

    def test_import_rejects_unsupported_type(
        self,
    ):
        batch = self.make_batch(
            migration_type="VENDORS",
        )

        with self.assertRaises(
            MigrationImportError
        ):
            (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

    def test_import_rejects_non_importable_validation(
        self,
    ):
        batch = self.make_batch(
            can_import=False,
        )

        with self.assertRaises(
            MigrationImportError
        ):
            (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

    def test_import_rejects_invalid_row(
        self,
    ):
        batch = self.make_batch(
            rows=[
                {
                    "row_number": 2,
                    "valid": False,
                    "errors": [
                        {
                            "field": "sku",
                            "code":
                                "INVALID_SKU",
                            "message":
                                "Invalid SKU.",
                        },
                    ],
                    "normalized": None,
                },
            ],
        )

        with self.assertRaises(
            MigrationImportError
        ):
            (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

    # ==================================================
    # CATEGORY IMPORT
    # ==================================================

    def test_category_import_uses_category_api_service(
        self,
    ):
        batch = self.make_batch(
            migration_type="CATEGORIES",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "name": "Electronics",
                        "description":
                            "Electronic items",
                    },
                },
            ],
        )

        created_category = (
            SimpleNamespace(
                id="category-created",
            )
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                CategoryAPIService,
                "create_category",
                return_value=(
                    created_category
                ),
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        create_mock.assert_called_once_with(
            organization=self.organization,
            payload={
                "name": "Electronics",
                "description":
                    "Electronic items",
            },
        )

        self.assertEqual(
            result["import"][
                "imported_rows"
            ],
            1,
        )

        self.assertEqual(
            result["import"][
                "failed_rows"
            ],
            0,
        )

        complete_mock.assert_called_once()

    # ==================================================
    # PRODUCT IMPORT
    # ==================================================

    def test_product_import_uses_product_api_service(
        self,
    ):
        batch = self.make_batch()

        created_product = (
            SimpleNamespace(
                id="product-created",
            )
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                ProductAPIService,
                "create_product",
                return_value=(
                    created_product
                ),
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        create_mock.assert_called_once_with(
            organization=self.organization,
            payload={
                "sku": "SKU-001",
                "name": "Test Product",
                "description": "",
                "category_id":
                    "category-1",
                "brand": "Test Brand",
                "unit": "PCS",
                "cost_price": "100.00",
                "selling_price":
                    "150.00",
                "barcode": "",
            },
        )

        self.assertEqual(
            result["import"][
                "imported_rows"
            ],
            1,
        )

        self.assertEqual(
            result["import"][
                "failed_rows"
            ],
            0,
        )

        complete_mock.assert_called_once()

    def test_duplicate_product_row_can_be_skipped(
        self,
    ):
        batch = self.make_batch(
            migration_type="PRODUCTS",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [
                        {
                            "field": "sku",
                            "code": "ALREADY_EXISTS",
                            "message": (
                                "A product with this "
                                "SKU already exists."
                            ),
                        },
                    ],
                    "skipped": True,
                    "normalized": {
                        "sku": "SKU-001",
                        "name": "Test Product",
                        "description": "",
                        "category": self.category,
                        "category_name": "Electronics",
                        "brand": "Test Brand",
                        "unit": "PCS",
                        "cost_price": "100.00",
                        "selling_price": "150.00",
                        "barcode": "",
                    },
                },
            ],
            options={
                "skip_duplicates": True,
            },
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                ProductAPIService,
                "create_product",
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        create_mock.assert_not_called()

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "SKIPPED",
                "reason": "ALREADY_EXISTS",
            },
        )

        complete_mock.assert_called_once()
    # ==================================================
    # ROW FAILURE
    # ==================================================

    def test_failed_row_is_recorded(
        self,
    ):
        batch = self.make_batch()

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                ProductAPIService,
                "create_product",
                side_effect=ValueError(
                    "Product creation failed."
                ),
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        import_result = result["import"]

        self.assertEqual(
            import_result[
                "imported_rows"
            ],
            0,
        )

        self.assertEqual(
            import_result[
                "failed_rows"
            ],
            1,
        )

        self.assertEqual(
            import_result["rows"][0][
                "status"
            ],
            "FAILED",
        )

        self.assertEqual(
            import_result["rows"][0][
                "error"
            ],
            "Product creation failed.",
        )

        complete_mock.assert_called_once()

    # ==================================================
    # MULTIPLE ROWS
    # ==================================================

    def test_import_counts_multiple_rows(
        self,
    ):
        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "name": "Category A",
                    "description": "",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "name": "Category B",
                    "description": "",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="CATEGORIES",
            rows=rows,
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                CategoryAPIService,
                "create_category",
                side_effect=[
                    SimpleNamespace(
                        id="category-a",
                    ),
                    SimpleNamespace(
                        id="category-b",
                    ),
                ],
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ),
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"][
                "imported_rows"
            ],
            2,
        )

        self.assertEqual(
            result["import"][
                "failed_rows"
            ],
            0,
        )

        self.assertEqual(
            len(
                result["import"]["rows"]
            ),
            2,
        )

    def test_completion_failure_marks_import_failed(
        self,
    ):
        batch = self.make_batch(
            migration_type="CATEGORIES",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "name": "Electronics",
                        "description": "",
                    },
                },
            ],
        )

        created_category = (
            SimpleNamespace(
                id="category-created",
            )
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                CategoryAPIService,
                "create_category",
                return_value=(
                    created_category
                ),
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                side_effect=RuntimeError(
                    "Completion persistence failed."
                ),
            ) as complete_mock,
            patch.object(
                MigrationBatchService,
                "fail_import",
                return_value=batch,
            ) as fail_mock,
        ):
            with self.assertRaisesRegex(
                MigrationImportError,
                "Completion persistence failed",
            ):
                (
                    MigrationImportService
                    .import_batch(
                        organization=(
                            self.organization
                        ),
                        batch=batch,
                    )
                )

        complete_mock.assert_called_once()

        fail_mock.assert_called_once_with(
            batch=batch,
            error_summary=(
                "Completion persistence failed."
            ),
        )

    def test_skipped_duplicate_is_not_imported(
        self,
    ):
        batch = self.make_batch(
            migration_type="CATEGORIES",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "skipped": True,
                    "errors": [
                        {
                            "code":
                                "ALREADY_EXISTS",
                            "message":
                                "Category already exists.",
                        },
                    ],
                    "normalized": {
                        "name": "Electronics",
                        "description": "",
                    },
                },
            ],
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                CategoryAPIService,
                "create_category",
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        self.assertIs(
            result["batch"],
            batch,
        )

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "status"
            ],
            "SKIPPED",
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "reason"
            ],
            "ALREADY_EXISTS",
        )

        create_mock.assert_not_called()

        complete_mock.assert_called_once()

        complete_kwargs = (
            complete_mock
            .call_args
            .kwargs
        )

        self.assertEqual(
            complete_kwargs[
                "imported_rows"
            ],
            0,
        )

        self.assertEqual(
            complete_kwargs[
                "skipped_rows"
            ],
            1,
        )

        self.assertEqual(
            complete_kwargs[
                "failed_rows"
            ],
            0,
        )

        import_result = (
            complete_kwargs[
                "import_result"
            ]
        )

        self.assertEqual(
            import_result["rows"][0][
                "status"
            ],
            "SKIPPED",
        )

        self.assertEqual(
            import_result["rows"][0][
                "reason"
            ],
            "ALREADY_EXISTS",
        )

    def test_customer_import_uses_customer_repository(
        self,
    ):
        batch = self.make_batch(
            migration_type="CUSTOMERS",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "code": "CUST-001",
                        "name": "Acme India",
                        "email": "sales@acme.com",
                        "phone": "9876543210",
                        "gstin":
                            "27ABCDE1234F1Z5",
                        "billing_address":
                            "Pune Office",
                        "shipping_address":
                            "Mumbai Warehouse",
                        "city": "Pune",
                        "state": "Maharashtra",
                        "country": "India",
                        "pincode": "411001",
                    },
                },
            ],
        )

        created_customer = (
            SimpleNamespace(
                id="customer-created",
            )
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                CustomerRepository,
                "create_customer",
                return_value=(
                    created_customer
                ),
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        create_mock.assert_called_once_with(
            organization=self.organization,
            code="CUST-001",
            name="Acme India",
            email="sales@acme.com",
            phone="9876543210",
            gstin="27ABCDE1234F1Z5",
            billing_address="Pune Office",
            shipping_address=(
                "Mumbai Warehouse"
            ),
            city="Pune",
            state="Maharashtra",
            country="India",
            pincode="411001",
        )

        self.assertEqual(
            result["import"][
                "migration_type"
            ],
            "CUSTOMERS",
        )

        self.assertEqual(
            result["import"][
                "imported_rows"
            ],
            1,
        )

        self.assertEqual(
            result["import"][
                "skipped_rows"
            ],
            0,
        )

        self.assertEqual(
            result["import"][
                "failed_rows"
            ],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "IMPORTED",
                "id": "customer-created",
            },
        )

        complete_mock.assert_called_once()


    def test_skipped_customer_is_not_imported(
        self,
    ):
        batch = self.make_batch(
            migration_type="CUSTOMERS",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "skipped": True,
                    "errors": [
                        {
                            "field": "code",
                            "code":
                                "ALREADY_EXISTS",
                            "message":
                                (
                                    "A customer with "
                                    "this code already "
                                    "exists."
                                ),
                        },
                    ],
                    "normalized": {
                        "code": "CUST-001",
                        "name": "Acme India",
                        "email": "",
                        "phone": "",
                        "gstin": "",
                        "billing_address": "",
                        "shipping_address": "",
                        "city": "",
                        "state": "",
                        "country": "India",
                        "pincode": "",
                    },
                },
            ],
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                CustomerRepository,
                "create_customer",
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ),
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        create_mock.assert_not_called()

        self.assertEqual(
            result["import"][
                "imported_rows"
            ],
            0,
        )

        self.assertEqual(
            result["import"][
                "skipped_rows"
            ],
            1,
        )

        self.assertEqual(
            result["import"][
                "failed_rows"
            ],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "SKIPPED",
                "reason": "ALREADY_EXISTS",
            },
        )

    def test_customer_import_failure_is_recorded(
        self,
    ):
        batch = self.make_batch(
            migration_type="CUSTOMERS",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "code": "CUST-001",
                        "name": "Acme India",
                        "email": "",
                        "phone": "",
                        "gstin": "",
                        "billing_address": "",
                        "shipping_address": "",
                        "city": "",
                        "state": "",
                        "country": "India",
                        "pincode": "",
                    },
                },
            ],
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                CustomerRepository,
                "create_customer",
                side_effect=ValueError(
                    "Customer creation failed."
                ),
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"][
                "imported_rows"
            ],
            0,
        )

        self.assertEqual(
            result["import"][
                "skipped_rows"
            ],
            0,
        )

        self.assertEqual(
            result["import"][
                "failed_rows"
            ],
            1,
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "row_number"
            ],
            2,
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "status"
            ],
            "FAILED",
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "error"
            ],
            "Customer creation failed.",
        )

        complete_mock.assert_called_once()

    # ==================================================
    # SUPPLIER IMPORT
    # ==================================================

    def test_supplier_import_uses_supplier_repository(
        self,
    ):
        batch = self.make_batch(
            migration_type="SUPPLIERS",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "code": "SUP-001",
                        "name": "ABC Components India",
                        "email": "sales@abc.com",
                        "phone": "9876543210",
                        "gstin": "27ABCDE1234F1Z5",
                        "address": "Pune Office",
                        "city": "Pune",
                        "state": "Maharashtra",
                        "country": "India",
                        "pincode": "411001",
                    },
                },
            ],
        )

        created_supplier = SimpleNamespace(
            id="supplier-created",
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                SupplierRepository,
                "create_supplier",
                return_value=created_supplier,
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        create_mock.assert_called_once_with(
            organization=self.organization,
            code="SUP-001",
            name="ABC Components India",
            email="sales@abc.com",
            phone="9876543210",
            gstin="27ABCDE1234F1Z5",
            address="Pune Office",
            city="Pune",
            state="Maharashtra",
            country="India",
            pincode="411001",
        )

        self.assertEqual(
            result["import"]["migration_type"],
            "SUPPLIERS",
        )

        self.assertEqual(
            result["import"]["imported_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "IMPORTED",
                "id": "supplier-created",
            },
        )

        complete_mock.assert_called_once()

    def test_skipped_supplier_is_not_imported(
        self,
    ):
        batch = self.make_batch(
            migration_type="SUPPLIERS",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "skipped": True,
                    "errors": [
                        {
                            "field": "code",
                            "code": "ALREADY_EXISTS",
                            "message": (
                                "A supplier with this "
                                "code already exists."
                            ),
                        },
                    ],
                    "normalized": {
                        "code": "SUP-001",
                        "name": "ABC Components India",
                        "email": "",
                        "phone": "",
                        "gstin": "",
                        "address": "",
                        "city": "",
                        "state": "",
                        "country": "India",
                        "pincode": "",
                    },
                },
            ],
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                SupplierRepository,
                "create_supplier",
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ),
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        create_mock.assert_not_called()

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "SKIPPED",
                "reason": "ALREADY_EXISTS",
            },
        )

    def test_supplier_import_failure_is_recorded(
        self,
    ):
        batch = self.make_batch(
            migration_type="SUPPLIERS",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "code": "SUP-001",
                        "name": "ABC Components India",
                        "email": "",
                        "phone": "",
                        "gstin": "",
                        "address": "",
                        "city": "",
                        "state": "",
                        "country": "India",
                        "pincode": "",
                    },
                },
            ],
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                SupplierRepository,
                "create_supplier",
                side_effect=ValueError(
                    "Supplier creation failed."
                ),
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "row_number"
            ],
            2,
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "status"
            ],
            "FAILED",
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "error"
            ],
            "Supplier creation failed.",
        )

        complete_mock.assert_called_once()

    # ==================================================
    # WAREHOUSE IMPORT
    # ==================================================

    def test_warehouse_import_uses_warehouse_repository(
        self,
    ):
        batch = self.make_batch(
            migration_type="WAREHOUSES",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "code": "WH-001",
                        "name": "Pune Warehouse",
                        "address": "Pune Office",
                        "city": "Pune",
                        "state": "Maharashtra",
                        "country": "India",
                        "pincode": "411001",
                    },
                },
            ],
        )

        created_warehouse = SimpleNamespace(
            id="warehouse-created",
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                WarehouseRepository,
                "create_warehouse",
                return_value=created_warehouse,
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        create_mock.assert_called_once_with(
            organization=self.organization,
            code="WH-001",
            name="Pune Warehouse",
            address="Pune Office",
            city="Pune",
            state="Maharashtra",
            country="India",
            pincode="411001",
        )

        self.assertEqual(
            result["import"]["migration_type"],
            "WAREHOUSES",
        )

        self.assertEqual(
            result["import"]["imported_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "IMPORTED",
                "id": "warehouse-created",
            },
        )

        complete_mock.assert_called_once()

    def test_duplicate_warehouse_row_can_be_skipped(
        self,
    ):
        batch = self.make_batch(
            migration_type="WAREHOUSES",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "skipped": True,
                    "normalized": {
                        "code": "WH-001",
                        "name": "Pune Warehouse",
                    },
                },
            ],
            options={
                "skip_duplicates": True,
            },
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                WarehouseRepository,
                "create_warehouse",
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        create_mock.assert_not_called()

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "status"
            ],
            "SKIPPED",
        )

        complete_mock.assert_called_once()

    def test_warehouse_import_failure_is_recorded(
        self,
    ):
        batch = self.make_batch(
            migration_type="WAREHOUSES",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "code": "WH-001",
                        "name": "Pune Warehouse",
                        "address": "Pune Office",
                        "city": "Pune",
                        "state": "Maharashtra",
                        "country": "India",
                        "pincode": "411001",
                    },
                },
            ],
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                WarehouseRepository,
                "create_warehouse",
                side_effect=ValueError(
                    "Warehouse creation failed."
                ),
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "FAILED",
                "error": "Warehouse creation failed.",
            },
        )

        complete_mock.assert_called_once()

    # ==================================================
    # INVENTORY IMPORT
    # ==================================================

    def test_inventory_import_uses_inventory_api_service(
        self,
    ):
        product = SimpleNamespace(
            id="product-1",
        )
        warehouse = SimpleNamespace(
            id="warehouse-1",
        )

        batch = self.make_batch(
            migration_type="INVENTORY",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "product_sku": "SKU-001",
                        "product": product,
                        "warehouse_code": "WH-001",
                        "warehouse": warehouse,
                        "quantity": "25.50",
                    },
                },
            ],
        )

        created_inventory = SimpleNamespace(
            id="inventory-created",
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                InventoryAPIService,
                "create_inventory",
                return_value=created_inventory,
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            payload={
                "product_id": "product-1",
                "warehouse_id": "warehouse-1",
                "quantity": "25.50",
            },
        )

        self.assertEqual(
            result["import"]["migration_type"],
            "INVENTORY",
        )
        self.assertEqual(
            result["import"]["imported_rows"],
            1,
        )
        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )
        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )
        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "IMPORTED",
                "id": "inventory-created",
            },
        )

        complete_mock.assert_called_once()

    def test_duplicate_inventory_row_can_be_skipped(
        self,
    ):
        batch = self.make_batch(
            migration_type="INVENTORY",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "skipped": True,
                    "normalized": {
                        "product_sku": "SKU-001",
                        "warehouse_code": "WH-001",
                        "quantity": "25.50",
                    },
                },
            ],
            options={
                "skip_duplicates": True,
            },
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                InventoryAPIService,
                "create_inventory",
            ) as create_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        create_mock.assert_not_called()

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )
        self.assertEqual(
            result["import"]["skipped_rows"],
            1,
        )
        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )
        self.assertEqual(
            result["import"]["rows"][0][
                "status"
            ],
            "SKIPPED",
        )

        complete_mock.assert_called_once()

    def test_inventory_import_failure_is_recorded(
        self,
    ):
        product = SimpleNamespace(
            id="product-1",
        )
        warehouse = SimpleNamespace(
            id="warehouse-1",
        )

        batch = self.make_batch(
            migration_type="INVENTORY",
            rows=[
                {
                    "row_number": 2,
                    "valid": True,
                    "errors": [],
                    "normalized": {
                        "product_sku": "SKU-001",
                        "product": product,
                        "warehouse_code": "WH-001",
                        "warehouse": warehouse,
                        "quantity": "25.50",
                    },
                },
            ],
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                InventoryAPIService,
                "create_inventory",
                side_effect=ValueError(
                    "Inventory creation failed."
                ),
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )
        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )
        self.assertEqual(
            result["import"]["failed_rows"],
            1,
        )
        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "FAILED",
                "error":
                    "Inventory creation failed.",
            },
        )

        complete_mock.assert_called_once()

    # ==================================================
    # SALES ORDER IMPORT
    # ==================================================

    def test_sales_order_rows_are_grouped_by_so_number(
        self,
    ):
        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-001",
                    "customer_code": "MIG-CUST-001",
                    "warehouse_code": "MIG-WH-001",
                    "order_date": "2026-09-01",
                    "expected_delivery_date":
                        "2026-09-05",
                    "product_sku": "MIG-PROD-001",
                    "quantity": "2.00",
                    "unit_price": "100.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "Migration test",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-001",
                    "customer_code": "MIG-CUST-001",
                    "warehouse_code": "MIG-WH-001",
                    "order_date": "2026-09-01",
                    "expected_delivery_date":
                        "2026-09-05",
                    "product_sku": "MIG-PROD-002",
                    "quantity": "3.00",
                    "unit_price": "200.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "Migration test",
                },
            },
            {
                "row_number": 4,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-002",
                    "customer_code": "MIG-CUST-002",
                    "warehouse_code": "MIG-WH-002",
                    "order_date": "2026-09-02",
                    "expected_delivery_date":
                        "2026-09-06",
                    "product_sku": "MIG-PROD-003",
                    "quantity": "1.00",
                    "unit_price": "300.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="SALES_ORDERS",
            rows=rows,
            created_by=self.user,
        )

        entities = [
            SimpleNamespace(
                id="sales-order-1",
            ),
            SimpleNamespace(
                id="sales-order-2",
            ),
        ]

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                MigrationImportService,
                "_import_sales_order_group",
                side_effect=entities,
            ) as import_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            import_mock.call_count,
            2,
        )

        first_call = (
            import_mock.call_args_list[0]
        )

        second_call = (
            import_mock.call_args_list[1]
        )

        self.assertEqual(
            len(
                first_call.kwargs[
                    "rows"
                ]
            ),
            2,
        )

        self.assertEqual(
            {
                row["normalized"]["so_number"]
                for row in first_call.kwargs[
                    "rows"
                ]
            },
            {
                "MIG-SO-001",
            },
        )

        self.assertEqual(
            len(
                second_call.kwargs[
                    "rows"
                ]
            ),
            1,
        )

        self.assertEqual(
            second_call.kwargs[
                "rows"
            ][0]["normalized"]["so_number"],
            "MIG-SO-002",
        )

        self.assertIs(
            first_call.kwargs[
                "organization"
            ],
            self.organization,
        )

        self.assertIs(
            first_call.kwargs[
                "created_by"
            ],
            self.user,
        )

        self.assertEqual(
            result["import"]["imported_rows"],
            3,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            len(
                result["import"]["rows"]
            ),
            3,
        )

        self.assertEqual(
            result["import"]["rows"][0][
                "id"
            ],
            "sales-order-1",
        )

        self.assertEqual(
            result["import"]["rows"][1][
                "id"
            ],
            "sales-order-1",
        )

        self.assertEqual(
            result["import"]["rows"][2][
                "id"
            ],
            "sales-order-2",
        )

        complete_mock.assert_called_once()

    def test_sales_order_group_failure_marks_all_group_rows_failed(
        self,
    ):
        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-001",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-001",
                },
            },
            {
                "row_number": 4,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-002",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="SALES_ORDERS",
            rows=rows,
        )

        def import_group(
            *,
            organization,
            created_by,
            rows,
        ):
            so_number = (
                rows[0]["normalized"][
                    "so_number"
                ]
            )

            if so_number == "MIG-SO-001":
                return SimpleNamespace(
                    id="sales-order-1",
                )

            raise MigrationImportError(
                "Sales order creation failed."
            )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                MigrationImportService,
                "_import_sales_order_group",
                side_effect=import_group,
            ),
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"]["imported_rows"],
            2,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        failed = [
            row
            for row in result["import"]["rows"]
            if row["status"] == "FAILED"
        ]

        self.assertEqual(
            len(failed),
            1,
        )

        self.assertEqual(
            failed[0]["row_number"],
            4,
        )

        self.assertEqual(
            failed[0]["so_number"],
            "MIG-SO-002",
        )

        self.assertEqual(
            failed[0]["error"],
            "Sales order creation failed.",
        )

        complete_mock.assert_called_once()

    def test_sales_order_skipped_row_is_not_imported(
        self,
    ):
        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "skipped": True,
                "normalized": {
                    "so_number": "MIG-SO-001",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-001",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="SALES_ORDERS",
            rows=rows,
        )

        entity = SimpleNamespace(
            id="sales-order-1",
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                MigrationImportService,
                "_import_sales_order_group",
                return_value=entity,
            ) as import_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ),
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        import_mock.assert_called_once()

        imported_group = (
            import_mock.call_args.kwargs[
                "rows"
            ]
        )

        self.assertEqual(
            len(imported_group),
            1,
        )

        self.assertEqual(
            imported_group[0][
                "row_number"
            ],
            3,
        )

        self.assertEqual(
            result["import"]["imported_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0],
            {
                "row_number": 2,
                "status": "SKIPPED",
                "reason": "ALREADY_EXISTS",
            },
        )

    def test_sales_order_import_does_not_use_standard_row_dispatch(
        self,
    ):
        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "so_number": "MIG-SO-001",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="SALES_ORDERS",
            rows=rows,
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                MigrationImportService,
                "_import_row",
            ) as standard_mock,
            patch.object(
                MigrationImportService,
                "_import_sales_order_group",
                return_value=SimpleNamespace(
                    id="sales-order-1",
                ),
            ) as sales_order_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ),
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        standard_mock.assert_not_called()

        sales_order_mock.assert_called_once()

        self.assertEqual(
            result["import"]["imported_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

    def test_import_sales_order_group_creates_one_order_with_multiple_items(
        self,
    ):
        customer = SimpleNamespace(
            id="customer-1",
            code="MIG-CUST-001",
        )

        warehouse = SimpleNamespace(
            id="warehouse-1",
            code="MIG-WH-001",
        )

        product_1 = SimpleNamespace(
            id="product-1",
            sku="MIG-PROD-001",
        )

        product_2 = SimpleNamespace(
            id="product-2",
            sku="MIG-PROD-002",
        )

        item_1 = SimpleNamespace(
            product=product_1,
            quantity="2.00",
        )

        item_2 = SimpleNamespace(
            product=product_2,
            quantity="3.00",
        )

        calculated = {
            "items": [
                item_1,
                item_2,
            ],
            "subtotal": "800.00",
            "tax_amount": "144.00",
            "discount_amount": "0.00",
            "total_amount": "944.00",
        }

        created_order = SimpleNamespace(
            id="sales-order-1",
            so_number="MIG-SO-001",
        )

        rows = [
            {
                "row_number": 2,
                "normalized": {
                    "so_number":
                        "MIG-SO-001",
                    "customer_code":
                        "MIG-CUST-001",
                    "warehouse_code":
                        "MIG-WH-001",
                    "order_date":
                        "2026-09-29",
                    "expected_delivery_date":
                        "2026-10-05",
                    "product_sku":
                        "MIG-PROD-001",
                    "quantity":
                        "2.00",
                    "unit_price":
                        "100.00",
                    "tax_rate":
                        "18.00",
                    "discount":
                        "0.00",
                    "notes":
                        "Migration order",
                },
            },
            {
                "row_number": 3,
                "normalized": {
                    "so_number":
                        "MIG-SO-001",
                    "customer_code":
                        "MIG-CUST-001",
                    "warehouse_code":
                        "MIG-WH-001",
                    "order_date":
                        "2026-09-29",
                    "expected_delivery_date":
                        "2026-10-05",
                    "product_sku":
                        "MIG-PROD-002",
                    "quantity":
                        "3.00",
                    "unit_price":
                        "200.00",
                    "tax_rate":
                        "18.00",
                    "discount":
                        "0.00",
                    "notes":
                        "Migration order",
                },
            },
        ]

        with (
            patch.object(
                SalesOrderRepository,
                "get_by_so_number",
                return_value=None,
            ) as existing_mock,
            patch.object(
                CustomerRepository,
                "get_by_code",
                return_value=customer,
            ) as customer_mock,
            patch.object(
                WarehouseRepository,
                "get_by_code",
                return_value=warehouse,
            ) as warehouse_mock,
            patch.object(
                ProductRepository,
                "get_by_sku",
                side_effect=[
                    product_1,
                    product_2,
                ],
            ) as product_mock,
            patch.object(
                SalesOrderService,
                "_build_items",
                return_value=calculated,
            ) as build_mock,
            patch.object(
                SalesOrderRepository,
                "create_sales_order",
                return_value=created_order,
            ) as create_mock,
        ):
            result = (
                MigrationImportService
                ._import_sales_order_group(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    rows=rows,
                )
            )

        self.assertIs(
            result,
            created_order,
        )

        existing_mock.assert_called_once_with(
            organization=self.organization,
            so_number="MIG-SO-001",
        )

        customer_mock.assert_called_once_with(
            organization=self.organization,
            code="MIG-CUST-001",
        )

        warehouse_mock.assert_called_once_with(
            organization=self.organization,
            code="MIG-WH-001",
        )

        self.assertEqual(
            product_mock.call_count,
            2,
        )

        self.assertEqual(
            product_mock.call_args_list[
                0
            ].kwargs,
            {
                "organization":
                    self.organization,
                "sku":
                    "MIG-PROD-001",
            },
        )

        self.assertEqual(
            product_mock.call_args_list[
                1
            ].kwargs,
            {
                "organization":
                    self.organization,
                "sku":
                    "MIG-PROD-002",
            },
        )

        build_mock.assert_called_once()

        raw_items = (
            build_mock.call_args.kwargs[
                "raw_items"
            ]
        )

        self.assertEqual(
            len(raw_items),
            2,
        )

        self.assertIs(
            raw_items[0]["product"],
            product_1,
        )

        self.assertEqual(
            raw_items[0]["quantity"],
            "2.00",
        )

        self.assertEqual(
            raw_items[0]["unit_price"],
            "100.00",
        )

        self.assertEqual(
            raw_items[0]["tax_rate"],
            "18.00",
        )

        self.assertEqual(
            raw_items[0]["discount"],
            "0.00",
        )

        self.assertIs(
            raw_items[1]["product"],
            product_2,
        )

        self.assertEqual(
            raw_items[1]["quantity"],
            "3.00",
        )

        self.assertEqual(
            raw_items[1]["unit_price"],
            "200.00",
        )

        create_mock.assert_called_once()

        create_kwargs = (
            create_mock.call_args.kwargs
        )

        self.assertIs(
            create_kwargs[
                "organization"
            ],
            self.organization,
        )

        self.assertEqual(
            create_kwargs[
                "so_number"
            ],
            "MIG-SO-001",
        )

        self.assertIs(
            create_kwargs[
                "customer"
            ],
            customer,
        )

        self.assertIs(
            create_kwargs[
                "warehouse"
            ],
            warehouse,
        )

        self.assertEqual(
            create_kwargs[
                "items"
            ],
            [
                item_1,
                item_2,
            ],
        )

        self.assertEqual(
            create_kwargs[
                "subtotal"
            ],
            "800.00",
        )

        self.assertEqual(
            create_kwargs[
                "tax_amount"
            ],
            "144.00",
        )

        self.assertEqual(
            create_kwargs[
                "discount_amount"
            ],
            "0.00",
        )

        self.assertEqual(
            create_kwargs[
                "total_amount"
            ],
            "944.00",
        )

        self.assertEqual(
            create_kwargs[
                "notes"
            ],
            "Migration order",
        )

        self.assertIs(
            create_kwargs[
                "created_by"
            ],
            self.user,
        )

        self.assertEqual(
            create_kwargs[
                "status"
            ],
            "DRAFT",
        )

        # Dates must have been converted from
        # persisted ISO strings back to datetime.
        self.assertEqual(
            create_kwargs[
                "order_date"
            ].year,
            2026,
        )

        self.assertEqual(
            create_kwargs[
                "order_date"
            ].month,
            9,
        )

        self.assertEqual(
            create_kwargs[
                "order_date"
            ].day,
            29,
        )

        self.assertEqual(
            create_kwargs[
                "expected_delivery_date"
            ].year,
            2026,
        )

        self.assertEqual(
            create_kwargs[
                "expected_delivery_date"
            ].month,
            10,
        )

        self.assertEqual(
            create_kwargs[
                "expected_delivery_date"
            ].day,
            5,
        )

    # ==================================================
    # PURCHASE ORDER IMPORT
    # ==================================================

    def test_purchase_order_rows_are_grouped_by_po_number(
        self,
    ):
        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "po_number": "MIG-PO-001",
                    "supplier_code": "MIG-SUP-001",
                    "order_date": "2026-09-01",
                    "expected_delivery_date":
                        "2026-09-05",
                    "product_sku": "MIG-PROD-001",
                    "quantity": "2.00",
                    "unit_price": "100.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "Migration test",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "po_number": "MIG-PO-001",
                    "supplier_code": "MIG-SUP-001",
                    "order_date": "2026-09-01",
                    "expected_delivery_date":
                        "2026-09-05",
                    "product_sku": "MIG-PROD-002",
                    "quantity": "3.00",
                    "unit_price": "200.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "Migration test",
                },
            },
            {
                "row_number": 4,
                "valid": True,
                "errors": [],
                "normalized": {
                    "po_number": "MIG-PO-002",
                    "supplier_code": "MIG-SUP-002",
                    "order_date": "2026-09-02",
                    "expected_delivery_date":
                        "2026-09-06",
                    "product_sku": "MIG-PROD-003",
                    "quantity": "1.00",
                    "unit_price": "300.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="PURCHASE_ORDERS",
            rows=rows,
            created_by=self.user,
        )

        entities = [
            SimpleNamespace(
                id="purchase-order-1",
            ),
            SimpleNamespace(
                id="purchase-order-2",
            ),
        ]

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                MigrationImportService,
                "_import_purchase_order_group",
                side_effect=entities,
            ) as import_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ) as complete_mock,
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            import_mock.call_count,
            2,
        )

        first_call = (
            import_mock.call_args_list[0]
        )

        second_call = (
            import_mock.call_args_list[1]
        )

        self.assertEqual(
            len(
                first_call.kwargs["rows"]
            ),
            2,
        )

        self.assertEqual(
            {
                row["normalized"]["po_number"]
                for row in first_call.kwargs[
                    "rows"
                ]
            },
            {
                "MIG-PO-001",
            },
        )

        self.assertEqual(
            len(
                second_call.kwargs["rows"]
            ),
            1,
        )

        self.assertEqual(
            second_call.kwargs[
                "rows"
            ][0]["normalized"]["po_number"],
            "MIG-PO-002",
        )

        self.assertIs(
            first_call.kwargs["organization"],
            self.organization,
        )

        self.assertIs(
            first_call.kwargs["created_by"],
            self.user,
        )

        self.assertEqual(
            result["import"]["imported_rows"],
            3,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            len(result["import"]["rows"]),
            3,
        )

        self.assertEqual(
            result["import"]["rows"][0]["id"],
            "purchase-order-1",
        )

        self.assertEqual(
            result["import"]["rows"][1]["id"],
            "purchase-order-1",
        )

        self.assertEqual(
            result["import"]["rows"][2]["id"],
            "purchase-order-2",
        )

        complete_mock.assert_called_once()

    def test_purchase_order_group_fails_for_different_supplier(
        self,
    ):
        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "po_number": "MIG-PO-001",
                    "supplier_code": "MIG-SUP-001",
                    "order_date": "2026-09-01",
                    "expected_delivery_date":
                        "2026-09-05",
                    "product_sku": "MIG-PROD-001",
                    "quantity": "2.00",
                    "unit_price": "100.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "po_number": "MIG-PO-001",
                    "supplier_code": "MIG-SUP-002",
                    "order_date": "2026-09-01",
                    "expected_delivery_date":
                        "2026-09-05",
                    "product_sku": "MIG-PROD-002",
                    "quantity": "1.00",
                    "unit_price": "200.00",
                    "tax_rate": "18.00",
                    "discount": "0.00",
                    "notes": "",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="PURCHASE_ORDERS",
            rows=rows,
            created_by=self.user,
        )

        with (
            patch.object(
                MigrationBatchService,
                "start_import",
                return_value=batch,
            ),
            patch.object(
                MigrationImportService,
                "_import_purchase_order_group",
                side_effect=MigrationImportError(
                    "Purchase order rows have "
                    "different suppliers."
                ),
            ) as import_mock,
            patch.object(
                MigrationBatchService,
                "complete_import",
                return_value=batch,
            ),
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        import_mock.assert_called_once()

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            2,
        )

        self.assertEqual(
            len(result["import"]["rows"]),
            2,
        )

        for row in result["import"]["rows"]:
            self.assertEqual(
                row["status"],
                "FAILED",
            )

            self.assertEqual(
                row["po_number"],
                "MIG-PO-001",
            )

            self.assertIn(
                "different suppliers",
                row["error"],
            )

    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    @patch.object(
        InvoiceService,
        "generate_from_sales_order",
    )
    def test_sales_invoice_import_uses_invoice_service(
        self,
        generate_invoice_mock,
        get_sales_order_mock,
    ):
        sales_order = SimpleNamespace(
            id="sales-order-1",
            status="FULFILLED",
        )

        invoice = SimpleNamespace(
            id="invoice-1",
            invoice_number="MIG-INV-001",
        )

        get_sales_order_mock.return_value = (
            sales_order
        )

        generate_invoice_mock.return_value = (
            invoice
        )

        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "invoice_number":
                        "MIG-INV-001",
                    "sales_order_number":
                        "MIG-SO-001",

                    # Simulate the BSON-safe persisted
                    # validation result. The importer
                    # must NOT rely on this value.
                    "sales_order":
                        "sales-order-1",

                    "invoice_date":
                        "2026-09-29",
                    "due_date":
                        "2026-10-29",
                    "notes":
                        "Migrated invoice",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="SALES_INVOICES",
            rows=rows,
            created_by=self.user,
        )

        with patch.object(
            MigrationBatchService,
            "start_import",
        ), patch.object(
            MigrationBatchService,
            "complete_import",
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"]["imported_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["rows"][0]["status"],
            "IMPORTED",
        )

        self.assertEqual(
            result["import"]["rows"][0]["id"],
            "invoice-1",
        )

        get_sales_order_mock.assert_called_once_with(
            organization=self.organization,
            so_number="MIG-SO-001",
        )

        generate_invoice_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            sales_order=sales_order,
            invoice_number="MIG-INV-001",
            invoice_date=datetime(
                2026,
                9,
                29,
            ).date(),
            due_date=datetime(
                2026,
                10,
                29,
            ).date(),
            notes="Migrated invoice",
        )


    @patch.object(
        SalesOrderRepository,
        "get_by_so_number",
    )
    @patch.object(
        InvoiceService,
        "generate_from_sales_order",
    )
    def test_sales_invoice_import_failure_is_recorded(
        self,
        generate_invoice_mock,
        get_sales_order_mock,
    ):
        sales_order = SimpleNamespace(
            id="sales-order-1",
            status="FULFILLED",
        )

        get_sales_order_mock.return_value = (
            sales_order
        )

        generate_invoice_mock.side_effect = (
            ValueError(
                "Invoice generation failed."
            )
        )

        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "invoice_number":
                        "MIG-INV-002",
                    "sales_order_number":
                        "MIG-SO-002",

                    # Persisted validation result
                    "sales_order":
                        "sales-order-1",

                    "invoice_date":
                        "2026-09-29",
                    "due_date":
                        "2026-10-29",
                    "notes": "",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="SALES_INVOICES",
            rows=rows,
            created_by=self.user,
        )

        with patch.object(
            MigrationBatchService,
            "start_import",
        ), patch.object(
            MigrationBatchService,
            "complete_import",
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            1,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        row_result = (
            result["import"]["rows"][0]
        )

        self.assertEqual(
            row_result["status"],
            "FAILED",
        )

        self.assertEqual(
            row_result["row_number"],
            2,
        )

        self.assertIn(
            "Invoice generation failed.",
            row_result["error"],
        )

        get_sales_order_mock.assert_called_once_with(
            organization=self.organization,
            so_number="MIG-SO-002",
        )

        generate_invoice_mock.assert_called_once()

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
    @patch.object(
        GoodsReceiptService,
        "receive_goods",
    )
    def test_goods_receipt_import_groups_items_into_one_grn(
        self,
        receive_goods_mock,
        get_purchase_order_mock,
        get_warehouse_mock,
        get_product_mock,
    ):
        purchase_order = SimpleNamespace(
            id="purchase-order-1",
            po_number="MIG-PO-003",
        )

        warehouse = SimpleNamespace(
            id="warehouse-1",
            code="MIG-WH-001",
        )

        product_1 = SimpleNamespace(
            id="product-1",
            sku="MIG-PROD-001",
        )

        product_2 = SimpleNamespace(
            id="product-2",
            sku="MIG-PROD-003",
        )

        goods_receipt = SimpleNamespace(
            id="goods-receipt-1",
            grn_number="GRN-MIG-001",
        )

        get_purchase_order_mock.return_value = (
            purchase_order
        )

        get_warehouse_mock.return_value = (
            warehouse
        )

        get_product_mock.side_effect = [
            product_1,
            product_2,
        ]

        receive_goods_mock.return_value = (
            goods_receipt
        )

        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "purchase_order_number":
                        "MIG-PO-003",
                    "warehouse_code":
                        "MIG-WH-001",
                    "product_sku":
                        "MIG-PROD-001",
                    "quantity_received":
                        "3.00",
                    "notes":
                        "Migrated GRN",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "purchase_order_number":
                        "MIG-PO-003",
                    "warehouse_code":
                        "MIG-WH-001",
                    "product_sku":
                        "MIG-PROD-003",
                    "quantity_received":
                        "2.00",
                    "notes":
                        "Migrated GRN",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="GOODS_RECEIPTS",
            rows=rows,
            created_by=self.user,
        )

        with patch.object(
            MigrationBatchService,
            "start_import",
        ), patch.object(
            MigrationBatchService,
            "complete_import",
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        # ------------------------------------------
        # COUNTS
        # ------------------------------------------

        self.assertEqual(
            result["import"]["imported_rows"],
            2,
        )

        self.assertEqual(
            result["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        # ------------------------------------------
        # ONE GRN SERVICE CALL
        # ------------------------------------------

        receive_goods_mock.assert_called_once()

        call = (
            receive_goods_mock.call_args
        )

        self.assertIs(
            call.kwargs["user"],
            self.user,
        )

        self.assertIs(
            call.kwargs["organization"],
            self.organization,
        )

        self.assertIs(
            call.kwargs["purchase_order"],
            purchase_order,
        )

        self.assertIs(
            call.kwargs["warehouse"],
            warehouse,
        )

        self.assertEqual(
            call.kwargs["notes"],
            "Migrated GRN",
        )

        # ------------------------------------------
        # TWO PRODUCTS INSIDE ONE GRN
        # ------------------------------------------

        raw_items = (
            call.kwargs["raw_items"]
        )

        self.assertEqual(
            len(raw_items),
            2,
        )

        self.assertIs(
            raw_items[0]["product"],
            product_1,
        )

        self.assertEqual(
            raw_items[0][
                "quantity_received"
            ],
            "3.00",
        )

        self.assertIs(
            raw_items[1]["product"],
            product_2,
        )

        self.assertEqual(
            raw_items[1][
                "quantity_received"
            ],
            "2.00",
        )

        # ------------------------------------------
        # REPOSITORY LOOKUPS
        # ------------------------------------------

        get_purchase_order_mock.assert_called_once_with(
            organization=self.organization,
            po_number="MIG-PO-003",
        )

        get_warehouse_mock.assert_called_once_with(
            organization=self.organization,
            code="MIG-WH-001",
        )

        self.assertEqual(
            get_product_mock.call_count,
            2,
        )

        get_product_mock.assert_any_call(
            organization=self.organization,
            sku="MIG-PROD-001",
        )

        get_product_mock.assert_any_call(
            organization=self.organization,
            sku="MIG-PROD-003",
        )

        # ------------------------------------------
        # BOTH SOURCE ROWS POINT TO SAME GRN
        # ------------------------------------------

        row_results = (
            result["import"]["rows"]
        )

        self.assertEqual(
            len(row_results),
            2,
        )

        for row_result in row_results:
            self.assertEqual(
                row_result["status"],
                "IMPORTED",
            )

            self.assertEqual(
                row_result["id"],
                "goods-receipt-1",
            )

            self.assertEqual(
                row_result["grn_number"],
                "GRN-MIG-001",
            )

            self.assertEqual(
                row_result[
                    "purchase_order_number"
                ],
                "MIG-PO-003",
            )

            self.assertEqual(
                row_result[
                    "warehouse_code"
                ],
                "MIG-WH-001",
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
    @patch.object(
        GoodsReceiptService,
        "receive_goods",
    )
    def test_goods_receipt_import_failure_is_recorded_for_group(
        self,
        receive_goods_mock,
        get_purchase_order_mock,
        get_warehouse_mock,
        get_product_mock,
    ):
        purchase_order = SimpleNamespace(
            id="purchase-order-1",
            po_number="MIG-PO-003",
        )

        warehouse = SimpleNamespace(
            id="warehouse-1",
            code="MIG-WH-001",
        )

        product_1 = SimpleNamespace(
            id="product-1",
            sku="MIG-PROD-001",
        )

        product_2 = SimpleNamespace(
            id="product-2",
            sku="MIG-PROD-003",
        )

        get_purchase_order_mock.return_value = (
            purchase_order
        )
        get_warehouse_mock.return_value = (
            warehouse
        )
        get_product_mock.side_effect = [
            product_1,
            product_2,
        ]

        receive_goods_mock.side_effect = ValueError(
            "Goods receipt creation failed."
        )

        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "purchase_order_number":
                        "MIG-PO-003",
                    "warehouse_code":
                        "MIG-WH-001",
                    "product_sku":
                        "MIG-PROD-001",
                    "quantity_received":
                        "3.00",
                    "notes": "",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "purchase_order_number":
                        "MIG-PO-003",
                    "warehouse_code":
                        "MIG-WH-001",
                    "product_sku":
                        "MIG-PROD-003",
                    "quantity_received":
                        "2.00",
                    "notes": "",
                },
            },
        ]

        batch = self.make_batch(
            migration_type="GOODS_RECEIPTS",
            rows=rows,
            created_by=self.user,
        )

        with patch.object(
            MigrationBatchService,
            "start_import",
        ), patch.object(
            MigrationBatchService,
            "complete_import",
        ):
            result = (
                MigrationImportService
                .import_batch(
                    organization=self.organization,
                    batch=batch,
                )
            )

        self.assertEqual(
            result["import"]["imported_rows"],
            0,
        )
        self.assertEqual(
            result["import"]["failed_rows"],
            2,
        )
        self.assertEqual(
            result["import"]["skipped_rows"],
            0,
        )

        receive_goods_mock.assert_called_once()

        self.assertEqual(
            len(result["import"]["rows"]),
            2,
        )

        for row in result["import"]["rows"]:
            self.assertEqual(
                row["status"],
                "FAILED",
            )
            self.assertIn(
                "Goods receipt creation failed.",
                row["error"],
            )

    @patch.object(
        MigrationImportService,
        "_import_goods_receipt_group",
    )
    def test_goods_receipt_import_creates_separate_groups(
        self,
        import_group_mock,
    ):
        import_group_mock.side_effect = [
            SimpleNamespace(
                id="grn-1",
                grn_number="GRN-001",
            ),
            SimpleNamespace(
                id="grn-2",
                grn_number="GRN-002",
            ),
        ]

        rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "purchase_order_number":
                        "MIG-PO-003",
                    "warehouse_code":
                        "MIG-WH-001",
                    "product_sku":
                        "MIG-PROD-001",
                    "quantity_received":
                        "3.00",
                    "notes": "",
                },
            },
            {
                "row_number": 3,
                "valid": True,
                "errors": [],
                "normalized": {
                    "purchase_order_number":
                        "MIG-PO-003",
                    "warehouse_code":
                        "MIG-WH-001",
                    "product_sku":
                        "MIG-PROD-003",
                    "quantity_received":
                        "2.00",
                    "notes": "",
                },
            },
            {
                "row_number": 4,
                "valid": True,
                "errors": [],
                "normalized": {
                    "purchase_order_number":
                        "MIG-PO-004",
                    "warehouse_code":
                        "MIG-WH-002",
                    "product_sku":
                        "MIG-PROD-002",
                    "quantity_received":
                        "5.00",
                    "notes": "",
                },
            },
        ]

        result = (
            MigrationImportService
            ._import_goods_receipt_rows(
                organization=self.organization,
                created_by=self.user,
                rows=rows,
            )
        )

        self.assertEqual(
            import_group_mock.call_count,
            2,
        )

        first_call = (
            import_group_mock.call_args_list[0]
        )
        second_call = (
            import_group_mock.call_args_list[1]
        )

        self.assertEqual(
            len(first_call.kwargs["rows"]),
            2,
        )
        self.assertEqual(
            len(second_call.kwargs["rows"]),
            1,
        )

        self.assertEqual(
            result["imported_rows"],
            3,
        )
        self.assertEqual(
            result["failed_rows"],
            0,
        )
        self.assertEqual(
            result["skipped_rows"],
            0,
        )

        self.assertEqual(
            result["rows"][0]["grn_number"],
            "GRN-001",
        )
        self.assertEqual(
            result["rows"][1]["grn_number"],
            "GRN-001",
        )
        self.assertEqual(
            result["rows"][2]["grn_number"],
            "GRN-002",
        )