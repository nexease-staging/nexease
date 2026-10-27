from unittest import TestCase

from apps.migration.services.migration_mapping_service import (
    MigrationMappingService,
)
from apps.migration.services.migration_schema_service import (
    MigrationSchemaError,
    MigrationSchemaService,
)
from apps.migration.services.migration_mapping_service import (
    MigrationMappingError,
    MigrationMappingService,
)

class MigrationSchemaServiceTestCase(
    TestCase,
):

    def test_product_required_fields(
        self,
    ):
        required = (
            MigrationSchemaService
            .required_fields(
                "PRODUCTS"
            )
        )

        self.assertEqual(
            required,
            [
                "sku",
                "name",
                "category",
                "unit",
            ],
        )

    def test_unknown_schema_rejected(
        self,
    ):
        with self.assertRaises(
            MigrationSchemaError
        ):
            (
                MigrationSchemaService
                .get_schema(
                    "UNKNOWN"
                )
            )

    def test_customer_schema(
        self,
    ):
        schema = (
            MigrationSchemaService
            .get_schema(
                "CUSTOMERS"
            )
        )

        self.assertEqual(
            schema["migration_type"],
            "CUSTOMERS",
        )

        self.assertEqual(
            schema["label"],
            "Customers",
        )

        fields = schema["fields"]

        self.assertEqual(
            set(fields.keys()),
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

        self.assertTrue(
            fields["code"]["required"]
        )

        self.assertTrue(
            fields["name"]["required"]
        )

        self.assertFalse(
            fields["email"]["required"]
        )

        self.assertFalse(
            fields["country"]["required"]
        )

    def test_supplier_schema(
        self,
    ):
        schema = (
            MigrationSchemaService
            .get_schema(
                "SUPPLIERS"
            )
        )

        self.assertEqual(
            schema["migration_type"],
            "SUPPLIERS",
        )

        self.assertEqual(
            schema["label"],
            "Suppliers",
        )

        self.assertEqual(
            MigrationSchemaService
            .required_fields(
                "SUPPLIERS"
            ),
            [
                "code",
                "name",
            ],
        )

        self.assertEqual(
            list(
                schema["fields"].keys()
            ),
            [
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
            ],
        )

    def test_warehouse_schema(
        self,
    ):
        schema = (
            MigrationSchemaService
            .get_schema(
                "WAREHOUSES"
            )
        )

        self.assertEqual(
            schema["migration_type"],
            "WAREHOUSES",
        )

        self.assertEqual(
            schema["label"],
            "Warehouses",
        )

        self.assertEqual(
            MigrationSchemaService
            .required_fields(
                "WAREHOUSES"
            ),
            [
                "code",
                "name",
            ],
        )

        self.assertEqual(
            list(
                schema["fields"].keys()
            ),
            [
                "code",
                "name",
                "address",
                "city",
                "state",
                "country",
                "pincode",
            ],
        )

    def test_inventory_schema_is_available(
        self,
    ):
        schema = (
            MigrationSchemaService
            .get_schema(
                "INVENTORY"
            )
        )

        self.assertEqual(
            schema["migration_type"],
            "INVENTORY",
        )

        self.assertEqual(
            schema["label"],
            "Opening Inventory",
        )

        self.assertEqual(
            MigrationSchemaService
            .required_fields(
                "INVENTORY"
            ),
            [
                "product_sku",
                "warehouse_code",
                "quantity",
            ],
        )

        self.assertEqual(
            list(
                schema["fields"].keys()
            ),
            [
                "product_sku",
                "warehouse_code",
                "quantity",
            ],
        )

class MigrationMappingServiceTestCase(
    TestCase,
):

    def test_product_mapping_suggestions(
        self,
    ):
        mapping = (
            MigrationMappingService
            .suggest_mapping(
                migration_type="PRODUCTS",
                source_columns=[
                    "Item Code",
                    "Item Name",
                    "Group",
                    "UOM",
                    "Purchase Rate",
                    "Sales Rate",
                ],
            )
        )

        self.assertEqual(
            mapping["sku"],
            "Item Code",
        )

        self.assertEqual(
            mapping["name"],
            "Item Name",
        )

        self.assertEqual(
            mapping["category"],
            "Group",
        )

        self.assertEqual(
            mapping["unit"],
            "UOM",
        )

        self.assertEqual(
            mapping["cost_price"],
            "Purchase Rate",
        )

        self.assertEqual(
            mapping["selling_price"],
            "Sales Rate",
        )

    def test_mapping_normalizes_underscores(
        self,
    ):
        mapping = (
            MigrationMappingService
            .suggest_mapping(
                migration_type="PRODUCTS",
                source_columns=[
                    "item_code",
                    "product_name",
                    "unit_of_measure",
                ],
            )
        )

        self.assertEqual(
            mapping["sku"],
            "item_code",
        )

        self.assertEqual(
            mapping["name"],
            "product_name",
        )

        self.assertEqual(
            mapping["unit"],
            "unit_of_measure",
        )

    def test_category_mapping_suggestion(
        self,
    ):
        mapping = (
            MigrationMappingService
            .suggest_mapping(
                migration_type="CATEGORIES",
                source_columns=[
                    "Group Name",
                    "Remarks",
                ],
            )
        )

        self.assertEqual(
            mapping,
            {
                "name": "Group Name",
                "description": "Remarks",
            },
        )

    def test_valid_product_mapping(
        self,
    ):
        result = (
            MigrationMappingService
            .validate_mapping(
                migration_type="PRODUCTS",
                source_columns=[
                    "Code",
                    "Name",
                    "Category",
                    "UOM",
                ],
                mapping={
                    "sku": "Code",
                    "name": "Name",
                    "category": "Category",
                    "unit": "UOM",
                },
            )
        )

        self.assertTrue(
            result["valid"]
        )

        self.assertEqual(
            result["errors"],
            [],
        )

    def test_required_mapping_missing(
        self,
    ):
        result = (
            MigrationMappingService
            .validate_mapping(
                migration_type="PRODUCTS",
                source_columns=[
                    "Code",
                    "Name",
                ],
                mapping={
                    "sku": "Code",
                    "name": "Name",
                },
            )
        )

        self.assertFalse(
            result["valid"]
        )

        codes = {
            error["code"]
            for error
            in result["errors"]
        }

        self.assertIn(
            "REQUIRED_MAPPING_MISSING",
            codes,
        )

    def test_unknown_source_column_rejected(
        self,
    ):
        result = (
            MigrationMappingService
            .validate_mapping(
                migration_type="PRODUCTS",
                source_columns=[
                    "Code",
                    "Name",
                    "UOM",
                ],
                mapping={
                    "sku": "Missing Code",
                    "name": "Name",
                    "unit": "UOM",
                },
            )
        )

        self.assertFalse(
            result["valid"]
        )

        codes = {
            error["code"]
            for error
            in result["errors"]
        }

        self.assertIn(
            "SOURCE_COLUMN_NOT_FOUND",
            codes,
        )

    def test_source_column_cannot_be_reused(
        self,
    ):
        result = (
            MigrationMappingService
            .validate_mapping(
                migration_type="PRODUCTS",
                source_columns=[
                    "Code",
                    "UOM",
                ],
                mapping={
                    "sku": "Code",
                    "name": "Code",
                    "unit": "UOM",
                },
            )
        )

        self.assertFalse(
            result["valid"]
        )

        codes = {
            error["code"]
            for error
            in result["errors"]
        }

        self.assertIn(
            "SOURCE_COLUMN_REUSED",
            codes,
        )

    def test_apply_mapping(
        self,
    ):
        rows = [
            {
                "Item Code": "ITEM-001",
                "Item Name": "Keyboard",
                "Group": "Electronics",
                "UOM": "PCS",
                "Unused": "Ignore me",
            },
            {
                "Item Code": "ITEM-002",
                "Item Name": "Mouse",
                "Group": "Electronics",
                "UOM": "PCS",
                "Unused": "Ignore me too",
            },
        ]

        mapping = {
            "sku": "Item Code",
            "name": "Item Name",
            "category": "Group",
            "unit": "UOM",
        }

        result = (
            MigrationMappingService
            .apply_mapping(
                rows=rows,
                mapping=mapping,
            )
        )

        self.assertEqual(
            result,
            [
                {
                    "sku": "ITEM-001",
                    "name": "Keyboard",
                    "category":
                        "Electronics",
                    "unit": "PCS",
                },
                {
                    "sku": "ITEM-002",
                    "name": "Mouse",
                    "category":
                        "Electronics",
                    "unit": "PCS",
                },
            ],
        )

    def test_apply_mapping_rejects_invalid_rows(
        self,
    ):
        with self.assertRaises(
            MigrationMappingError
        ):
            (
                MigrationMappingService
                .apply_mapping(
                    rows="invalid",
                    mapping={},
                )
            )

    def test_apply_mapping_rejects_non_object_row(
        self,
    ):
        with self.assertRaises(
            MigrationMappingError
        ):
            (
                MigrationMappingService
                .apply_mapping(
                    rows=[
                        "invalid-row",
                    ],
                    mapping={},
                )
            )

    def test_customer_mapping_suggestions(
        self,
    ):
        mapping = (
            MigrationMappingService
            .suggest_mapping(
                migration_type=(
                    "CUSTOMERS"
                ),
                source_columns=[
                    "Customer Code",
                    "Customer Name",
                    "Email Address",
                    "Mobile Number",
                    "GST Number",
                    "Billing Address",
                    "Shipping Address",
                    "City",
                    "State",
                    "Country",
                    "Pin Code",
                ],
            )
        )

        self.assertEqual(
            mapping["code"],
            "Customer Code",
        )

        self.assertEqual(
            mapping["name"],
            "Customer Name",
        )

        self.assertEqual(
            mapping["email"],
            "Email Address",
        )

        self.assertEqual(
            mapping["phone"],
            "Mobile Number",
        )

        self.assertEqual(
            mapping["gstin"],
            "GST Number",
        )

        self.assertEqual(
            mapping["billing_address"],
            "Billing Address",
        )

        self.assertEqual(
            mapping["shipping_address"],
            "Shipping Address",
        )

        self.assertEqual(
            mapping["city"],
            "City",
        )

        self.assertEqual(
            mapping["state"],
            "State",
        )

        self.assertEqual(
            mapping["country"],
            "Country",
        )

        self.assertEqual(
            mapping["pincode"],
            "Pin Code",
        )

    def test_supplier_mapping_suggestions(
        self,
    ):
        mapping = (
            MigrationMappingService
            .suggest_mapping(
                migration_type=(
                    "SUPPLIERS"
                ),
                source_columns=[
                    "Vendor Code",
                    "Vendor Name",
                    "Supplier Email",
                    "Phone Number",
                    "GST Number",
                    "Vendor Address",
                    "City",
                    "State",
                    "Country",
                    "Postal Code",
                ],
            )
        )

        self.assertEqual(
            mapping["code"],
            "Vendor Code",
        )

        self.assertEqual(
            mapping["name"],
            "Vendor Name",
        )

        self.assertEqual(
            mapping["email"],
            "Supplier Email",
        )

        self.assertEqual(
            mapping["phone"],
            "Phone Number",
        )

        self.assertEqual(
            mapping["gstin"],
            "GST Number",
        )

        self.assertEqual(
            mapping["address"],
            "Vendor Address",
        )

        self.assertEqual(
            mapping["city"],
            "City",
        )

        self.assertEqual(
            mapping["state"],
            "State",
        )

        self.assertEqual(
            mapping["country"],
            "Country",
        )

        self.assertEqual(
            mapping["pincode"],
            "Postal Code",
        )

    def test_warehouse_mapping_suggestions(
        self,
    ):
        mapping = (
            MigrationMappingService
            .suggest_mapping(
                migration_type=(
                    "WAREHOUSES"
                ),
                source_columns=[
                    "Warehouse Code",
                    "Warehouse Name",
                    "Warehouse Address",
                    "City",
                    "State",
                    "Country",
                    "Postal Code",
                ],
            )
        )

        self.assertEqual(
            mapping["code"],
            "Warehouse Code",
        )

        self.assertEqual(
            mapping["name"],
            "Warehouse Name",
        )

        self.assertEqual(
            mapping["address"],
            "Warehouse Address",
        )

        self.assertEqual(
            mapping["city"],
            "City",
        )

        self.assertEqual(
            mapping["state"],
            "State",
        )

        self.assertEqual(
            mapping["country"],
            "Country",
        )

        self.assertEqual(
            mapping["pincode"],
            "Postal Code",
        )

    def test_inventory_mapping_suggestions(
        self,
    ):
        mapping = (
            MigrationMappingService
            .suggest_mapping(
                migration_type="INVENTORY",
                source_columns=[
                    "SKU",
                    "Warehouse Code",
                    "Opening Stock",
                ],
            )
        )

        self.assertEqual(
            mapping["product_sku"],
            "SKU",
        )

        self.assertEqual(
            mapping["warehouse_code"],
            "Warehouse Code",
        )

        self.assertEqual(
            mapping["quantity"],
            "Opening Stock",
        )