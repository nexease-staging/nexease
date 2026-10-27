from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)
from datetime import datetime
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.services.sales_order_service import (
    SalesOrderService,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.sales.services.invoice_service import (
    InvoiceService,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)

from apps.purchasing.services.purchase_order_service import (
    PurchaseOrderService,
)
from apps.purchasing.services.goods_receipt_service import (
    GoodsReceiptService,
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
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)


class MigrationImportError(ValueError):
    """
    Raised when a validated migration cannot
    be safely imported.
    """
    pass

class MigrationImportService:

    SUPPORTED_TYPES = {
        "EMPLOYEES", "VENDOR_BILLS", "CUSTOMER_PAYMENTS", "SUPPLIER_PAYMENTS",
        "CATEGORIES",
        "PRODUCTS",
        "CUSTOMERS",
        "SUPPLIERS",
        "WAREHOUSES",
        "INVENTORY",
        "SALES_ORDERS",
        "PURCHASE_ORDERS",
        "SALES_INVOICES",
        "GOODS_RECEIPTS",
    }

    @staticmethod
    def _parse_sales_order_date(
        value,
        *,
        required=False,
    ):
        if value in (
            None,
            "",
        ):
            if required:
                raise MigrationImportError(
                    "Sales order date is unavailable."
                )

            return None

        if isinstance(
            value,
            datetime,
        ):
            return value

        try:
            return datetime.fromisoformat(
                str(value).strip()
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise MigrationImportError(
                "Validated sales order date "
                "is invalid."
            ) from exc

    @staticmethod
    def _parse_purchase_order_date(
        value,
        *,
        required=False,
    ):
        if value in (
            None,
            "",
        ):
            if required:
                raise MigrationImportError(
                    "Purchase order date is unavailable."
                )

            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        try:
            return datetime.fromisoformat(
                str(value).strip()
            ).date()

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise MigrationImportError(
                "Validated purchase order date "
                "is invalid."
            ) from exc

    @staticmethod
    def _parse_sales_invoice_date(
        value,
        *,
        required=False,
    ):
        if value in (
            None,
            "",
        ):
            if required:
                raise MigrationImportError(
                    "Sales invoice date is unavailable."
                )

            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        try:
            return datetime.fromisoformat(
                str(value).strip()
            ).date()

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise MigrationImportError(
                "Validated sales invoice date "
                "is invalid."
            ) from exc
    # ==================================================

    # VALIDATION RESULT

    # ==================================================



    @staticmethod

    def _get_validated_rows(

        *,

        batch,

    ):

        validation_result = (

            batch.validation_result

            or

            {}

        )



        if not isinstance(

            validation_result,

            dict,

        ):

            raise MigrationImportError(

                "Migration validation result "

                "is invalid."

            )



        if not validation_result.get(

            "can_import"

        ):

            raise MigrationImportError(

                "Migration is not ready "

                "for import."

            )



        rows = validation_result.get(

            "rows"

        )



        if not isinstance(

            rows,

            list,

        ):

            raise MigrationImportError(

                "Validated migration rows "

                "are unavailable."

            )



        if not rows:

            raise MigrationImportError(

                "Migration contains no "

                "validated rows."

            )



        normalized_rows = []



        for row in rows:

            if not isinstance(row, dict):

                raise MigrationImportError(

                    "Migration validation "

                    "row is invalid."

                )



            if not row.get("valid"):

                raise MigrationImportError(

                    "Migration contains "

                    "invalid rows."

                )



            normalized = row.get(

                "normalized"

            )



            if not isinstance(

                normalized,

                dict,

            ):

                raise MigrationImportError(

                    "Normalized migration "

                    "row is unavailable."

                )



            normalized_rows.append(

                {

                    "row_number":

                        row.get(

                            "row_number"

                        ),

                    "normalized":

                        normalized,

                    "skipped":

                        bool(

                            row.get(

                                "skipped",

                                False,

                            )

                        ),

                }

            )



        return normalized_rows



    # ==================================================

    # CATEGORY IMPORT

    # ==================================================



    @staticmethod

    def _import_category(

        *,

        organization,

        normalized,

    ):

        payload = {

            "name":

                normalized.get(

                    "name"

                ),

            "description":

                normalized.get(

                    "description",

                    "",

                ),

        }



        return (

            CategoryAPIService

            .create_category(

                organization=organization,

                payload=payload,

            )

        )



    # ==================================================

    # PRODUCT IMPORT

    # ==================================================

    @staticmethod
    def _import_product(
        *,
        organization,
        normalized,
    ):
        category = normalized.get("category")

        if category is None:
            raise MigrationImportError(
                "Validated product category "
                "is unavailable."
            )

        # Validation results are persisted before import.
        # A referenced category may therefore be either:
        #
        # - a live Category document, or
        # - its persisted string/ObjectId value.
        #
        # ProductAPIService expects category_id in the
        # incoming payload.
        if hasattr(category, "id"):
            category_id = str(category.id)
        else:
            category_id = str(category).strip()

        if not category_id:
            raise MigrationImportError(
                "Validated product category "
                "is unavailable."
            )

        payload = {
            "sku": normalized.get("sku"),
            "name": normalized.get("name"),
            "description": normalized.get(
                "description",
                "",
            ),
            "category_id": category_id,
            "brand": normalized.get(
                "brand",
                "",
            ),
            "unit": normalized.get("unit"),
            "cost_price": normalized.get(
                "cost_price"
            ),
            "selling_price": normalized.get(
                "selling_price"
            ),
            "barcode": normalized.get(
                "barcode",
                "",
            ),
        }

        return (
            ProductAPIService
            .create_product(
                organization=organization,
                payload=payload,
            )
        )

    # ==================================================

    # CUSTOMER IMPORT

    # ==================================================



    @staticmethod

    def _import_customer(

        *,

        organization,

        normalized,

    ):

        return (

            CustomerRepository

            .create_customer(

                organization=organization,

                code=normalized.get(

                    "code"

                ),

                name=normalized.get(

                    "name"

                ),

                email=normalized.get(

                    "email",

                    "",

                ),

                phone=normalized.get(

                    "phone",

                    "",

                ),

                gstin=normalized.get(

                    "gstin",

                    "",

                ),

                billing_address=(

                    normalized.get(

                        "billing_address",

                        "",

                    )

                ),

                shipping_address=(

                    normalized.get(

                        "shipping_address",

                        "",

                    )

                ),

                city=normalized.get(

                    "city",

                    "",

                ),

                state=normalized.get(

                    "state",

                    "",

                ),

                country=normalized.get(

                    "country",

                    "India",

                ),

                pincode=normalized.get(

                    "pincode",

                    "",

                ),

            )

        )



    # ==================================================

    # SUPPLIER IMPORT

    # ==================================================



    @staticmethod

    def _import_supplier(

        *,

        organization,

        normalized,

    ):

        return (

            SupplierRepository

            .create_supplier(

                organization=organization,

                code=normalized.get(

                    "code"

                ),

                name=normalized.get(

                    "name"

                ),

                email=normalized.get(

                    "email",

                    "",

                ),

                phone=normalized.get(

                    "phone",

                    "",

                ),

                gstin=normalized.get(

                    "gstin",

                    "",

                ),

                address=normalized.get(

                    "address",

                    "",

                ),

                city=normalized.get(

                    "city",

                    "",

                ),

                state=normalized.get(

                    "state",

                    "",

                ),

                country=normalized.get(

                    "country",

                    "India",

                ),

                pincode=normalized.get(

                    "pincode",

                    "",

                ),

            )

        )



    # ==================================================

    # WAREHOUSE IMPORT

    # ==================================================



    @staticmethod

    def _import_warehouse(

        *,

        organization,

        normalized,

    ):

        return (

            WarehouseRepository

            .create_warehouse(

                organization=organization,

                code=normalized.get(

                    "code"

                ),

                name=normalized.get(

                    "name"

                ),

                address=normalized.get(

                    "address",

                    "",

                ),

                city=normalized.get(

                    "city",

                    "",

                ),

                state=normalized.get(

                    "state",

                    "",

                ),

                country=normalized.get(

                    "country",

                    "India",

                ),

                pincode=normalized.get(

                    "pincode",

                    "",

                ),

            )

        )



    # ==================================================

    # INVENTORY IMPORT

    # ==================================================

    @staticmethod
    def _import_inventory(
        *,
        user,
        organization,
        normalized,
    ):
        product = normalized.get(
            "product"
        )
        warehouse = normalized.get(
            "warehouse"
        )

        if product is None:
            raise MigrationImportError(
                "Validated inventory row does "
                "not contain a product."
            )

        if warehouse is None:
            raise MigrationImportError(
                "Validated inventory row does "
                "not contain a warehouse."
            )

        # Validation results are persisted in MongoDB.
        #
        # During validation, product and warehouse may be
        # MongoEngine document instances. Once persisted,
        # however, they are stored as their string IDs.
        #
        # Support both forms so this importer works for:
        #
        # 1. freshly validated in-memory rows
        # 2. persisted validation_result rows
        product_id = str(
            getattr(
                product,
                "id",
                product,
            )
        )

        warehouse_id = str(
            getattr(
                warehouse,
                "id",
                warehouse,
            )
        )

        return (
            InventoryAPIService
            .create_inventory(
                user=user,
                organization=organization,
                payload={
                    "product_id":
                        product_id,

                    "warehouse_id":
                        warehouse_id,

                    "quantity":
                        normalized.get(
                            "quantity"
                        ),
                },
            )
        )

    # ==================================================
    # SALES ORDER IMPORT
    # ==================================================

    @classmethod
    def _import_purchase_order_group(
        cls,
        *,
        organization,
        created_by,
        rows,
    ):
        if not rows:
            raise MigrationImportError(
                "Purchase order rows are unavailable."
            )

        first = rows[0].get(
            "normalized",
            {},
        )

        po_number = str(
            first.get(
                "po_number",
                "",
            )
            or
            ""
        ).strip().upper()

        supplier_code = str(
            first.get(
                "supplier_code",
                "",
            )
            or
            ""
        ).strip().upper()

        if not po_number:
            raise MigrationImportError(
                "Validated purchase order number "
                "is unavailable."
            )

        supplier = (
            SupplierRepository
            .get_by_code(
                organization=organization,
                code=supplier_code,
            )
        )

        if supplier is None:
            raise MigrationImportError(
                "Validated purchase order supplier "
                "is unavailable."
            )

        order_date = (
            cls._parse_purchase_order_date(
                first.get("order_date"),
                required=True,
            )
        )

        expected_delivery_date = (
            cls._parse_purchase_order_date(
                first.get(
                    "expected_delivery_date"
                ),
                required=False,
            )
        )

        notes = str(
            first.get("notes") or ""
        ).strip()

        # All rows belonging to one PO must
        # describe the same PO header.
        for row in rows[1:]:
            normalized = row.get(
                "normalized",
                {},
            )

            row_supplier_code = str(
                normalized.get(
                    "supplier_code",
                    "",
                )
                or
                ""
            ).strip().upper()

            if row_supplier_code != supplier_code:
                raise MigrationImportError(
                    "Purchase order rows have "
                    "different suppliers."
                )

            row_order_date = (
                cls._parse_purchase_order_date(
                    normalized.get(
                        "order_date"
                    ),
                    required=True,
                )
            )

            if row_order_date != order_date:
                raise MigrationImportError(
                    "Purchase order rows have "
                    "different order dates."
                )

            row_delivery_date = (
                cls._parse_purchase_order_date(
                    normalized.get(
                        "expected_delivery_date"
                    ),
                    required=False,
                )
            )

            if (
                row_delivery_date
                != expected_delivery_date
            ):
                raise MigrationImportError(
                    "Purchase order rows have "
                    "different expected "
                    "delivery dates."
                )

        raw_items = []

        for row in rows:
            normalized = row.get(
                "normalized",
                {},
            )

            product_sku = str(
                normalized.get(
                    "product_sku",
                    "",
                )
                or
                ""
            ).strip().upper()

            product = (
                ProductRepository
                .get_by_sku(
                    organization=organization,
                    sku=product_sku,
                )
            )

            if product is None:
                raise MigrationImportError(
                    "Validated purchase order "
                    "product is unavailable."
                )

            raw_items.append(
                {
                    "product": product,
                    "quantity":
                        normalized.get(
                            "quantity"
                        ),
                    "unit_price":
                        normalized.get(
                            "unit_price"
                        ),
                    "tax_rate":
                        normalized.get(
                            "tax_rate"
                        )
                        or
                        "0",
                    "discount":
                        normalized.get(
                            "discount"
                        )
                        or
                        "0",
                }
            )

        # Reuse purchasing-domain calculations.
        calculated = (
            PurchaseOrderService
            ._build_items(
                organization=organization,
                raw_items=raw_items,
            )
        )

        existing = (
            PurchaseOrderRepository
            .get_by_po_number(
                organization=organization,
                po_number=po_number,
            )
        )

        if existing is not None:
            raise MigrationImportError(
                "Purchase order already exists."
            )

        return (
            PurchaseOrderRepository
            .create_purchase_order(
                organization=organization,
                po_number=po_number,
                supplier=supplier,
                order_date=order_date,
                expected_delivery_date=(
                    expected_delivery_date
                ),
                items=calculated["items"],
                subtotal=calculated["subtotal"],
                tax_amount=calculated[
                    "tax_amount"
                ],
                discount_amount=calculated[
                    "discount_amount"
                ],
                total_amount=calculated[
                    "total_amount"
                ],
                notes=notes,
                created_by=created_by,
                status="DRAFT",
            )
        )

    @staticmethod
    def _import_sales_order_group(
        *,
        organization,
        created_by,
        rows,
    ):
        if not rows:
            raise MigrationImportError(
                "Sales order migration group "
                "contains no rows."
            )

        first = rows[0]["normalized"]

        so_number = str(
            first.get(
                "so_number",
                "",
            )
        ).strip().upper()

        if not so_number:
            raise MigrationImportError(
                "Validated sales order number "
                "is unavailable."
            )

        existing = (
            SalesOrderRepository
            .get_by_so_number(
                organization=organization,
                so_number=so_number,
            )
        )

        if existing is not None:
            raise MigrationImportError(
                "Sales order already exists."
            )

        customer_code = str(
            first.get(
                "customer_code",
                "",
            )
        ).strip().upper()

        warehouse_code = str(
            first.get(
                "warehouse_code",
                "",
            )
        ).strip().upper()

        customer = (
            CustomerRepository
            .get_by_code(
                organization=organization,
                code=customer_code,
            )
        )

        if customer is None:
            raise MigrationImportError(
                "Validated sales order customer "
                "is unavailable."
            )

        warehouse = (
            WarehouseRepository
            .get_by_code(
                organization=organization,
                code=warehouse_code,
            )
        )

        if warehouse is None:
            raise MigrationImportError(
                "Validated sales order warehouse "
                "is unavailable."
            )

        order_date = (
            MigrationImportService
            ._parse_sales_order_date(
                first.get(
                    "order_date"
                ),
                required=True,
            )
        )

        expected_delivery_date = (
            MigrationImportService
            ._parse_sales_order_date(
                first.get(
                    "expected_delivery_date"
                )
            )
        )

        notes = str(
            first.get(
                "notes",
                "",
            )
            or ""
        ).strip()

        raw_items = []

        for row in rows:
            normalized = row["normalized"]

            # All lines belonging to one SO must
            # describe the same order header.
            if (
                str(
                    normalized.get(
                        "customer_code",
                        "",
                    )
                ).strip().upper()
                != customer_code
            ):
                raise MigrationImportError(
                    "Sales order lines contain "
                    "different customers."
                )

            if (
                str(
                    normalized.get(
                        "warehouse_code",
                        "",
                    )
                ).strip().upper()
                != warehouse_code
            ):
                raise MigrationImportError(
                    "Sales order lines contain "
                    "different warehouses."
                )

            product_sku = str(
                normalized.get(
                    "product_sku",
                    "",
                )
            ).strip().upper()

            product = (
                ProductRepository
                .get_by_sku(
                    organization=organization,
                    sku=product_sku,
                )
            )

            if product is None:
                raise MigrationImportError(
                    "Validated sales order product "
                    "is unavailable."
                )

            raw_items.append(
                {
                    "product": product,
                    "quantity":
                        normalized.get(
                            "quantity"
                        ),
                    "unit_price":
                        normalized.get(
                            "unit_price"
                        ),
                    "tax_rate":
                        normalized.get(
                            "tax_rate",
                            "0",
                        ),
                    "discount":
                        normalized.get(
                            "discount",
                            "0",
                        ),
                }
            )

        calculated = (
            SalesOrderService
            ._build_items(
                organization=organization,
                raw_items=raw_items,
            )
        )

        return (
            SalesOrderRepository
            .create_sales_order(
                organization=organization,
                so_number=so_number,
                customer=customer,
                warehouse=warehouse,
                order_date=order_date,
                expected_delivery_date=(
                    expected_delivery_date
                ),
                items=calculated["items"],
                subtotal=calculated[
                    "subtotal"
                ],
                tax_amount=calculated[
                    "tax_amount"
                ],
                discount_amount=calculated[
                    "discount_amount"
                ],
                total_amount=calculated[
                    "total_amount"
                ],
                notes=notes,
                created_by=created_by,
                status="DRAFT",
            )
        )

    @classmethod
    def _import_sales_invoice(
        cls,
        *,
        user,
        organization,
        normalized,
    ):
        # ==============================================
        # SALES ORDER
        # ==============================================

        sales_order_number = (
            str(
                normalized.get(
                    "sales_order_number",
                    "",
                )
                or ""
            )
            .strip()
            .upper()
        )

        if not sales_order_number:
            raise MigrationImportError(
                "Validated sales order number "
                "is unavailable."
            )

        sales_order = (
            SalesOrderRepository
            .get_by_so_number(
                organization=organization,
                so_number=sales_order_number,
            )
        )

        if sales_order is None:
            raise MigrationImportError(
                "Validated sales order "
                "could not be resolved."
            )

        # ==============================================
        # INVOICE NUMBER
        # ==============================================

        invoice_number = (
            str(
                normalized.get(
                    "invoice_number",
                    "",
                )
                or ""
            )
            .strip()
            .upper()
        )

        if not invoice_number:
            raise MigrationImportError(
                "Validated invoice number "
                "is unavailable."
            )

        # ==============================================
        # DATES
        # ==============================================

        invoice_date = (
            cls._parse_sales_invoice_date(
                normalized.get(
                    "invoice_date"
                ),
                required=True,
            )
        )

        due_date = (
            cls._parse_sales_invoice_date(
                normalized.get(
                    "due_date"
                ),
                required=False,
            )
        )

        # ==============================================
        # NOTES
        # ==============================================

        notes = (
            str(
                normalized.get(
                    "notes",
                    "",
                )
                or ""
            )
            .strip()
        )

        # ==============================================
        # CREATE INVOICE
        # ==============================================

        return (
            InvoiceService
            .generate_from_sales_order(
                user=user,
                organization=organization,
                sales_order=sales_order,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                due_date=due_date,
                notes=notes,
            )
        )
    # ==================================================

    # ROW DISPATCH

    # ==================================================



    @classmethod

    def _import_row(

        cls,

        *,

        user,

        organization,

        migration_type,

        normalized,

    ):

        if migration_type == "EMPLOYEES":
            from apps.migration.services.employee_import import import_employee
            return import_employee(user,organization,normalized)
        if migration_type in {"VENDOR_BILLS","CUSTOMER_PAYMENTS","SUPPLIER_PAYMENTS"}:
            from apps.migration.services.financial_import import import_financial
            return import_financial(user,organization,migration_type,normalized)
        if migration_type == "CATEGORIES":

            return cls._import_category(

                organization=organization,

                normalized=normalized,

            )



        if migration_type == "PRODUCTS":

            return cls._import_product(

                organization=organization,

                normalized=normalized,

            )



        if migration_type == "CUSTOMERS":

            return cls._import_customer(

                organization=organization,

                normalized=normalized,

            )



        if migration_type == "SUPPLIERS":

            return cls._import_supplier(

                organization=organization,

                normalized=normalized,

            )



        if migration_type == "WAREHOUSES":

            return cls._import_warehouse(

                organization=organization,

                normalized=normalized,

            )





        if migration_type == "INVENTORY":

            return cls._import_inventory(

                user=user,

                organization=organization,

                normalized=normalized,

            )

        if migration_type == "SALES_INVOICES":

            return cls._import_sales_invoice(
                user=user,
                organization=organization,
                normalized=normalized,
            )

        raise MigrationImportError(

            "Import is not available for "

            "this migration type."

        )

    @classmethod
    def _import_sales_order_rows(
        cls,
        *,
        organization,
        created_by,
        rows,
    ):
        """
        Import validated SALES_ORDERS rows.

        Multiple rows sharing the same SO number
        are imported as one SalesOrder containing
        multiple SalesOrderItems.
        """

        grouped = {}

        for row in rows:
            normalized = row.get(
                "normalized",
                {},
            )

            so_number = str(
                normalized.get(
                    "so_number",
                    "",
                )
                or
                ""
            ).strip().upper()

            if not so_number:
                raise MigrationImportError(
                    "Validated sales order number "
                    "is unavailable."
                )

            grouped.setdefault(
                so_number,
                [],
            ).append(row)

        imported_rows = 0
        skipped_rows = 0
        failed_rows = 0

        row_results = []

        for so_number, group_rows in grouped.items():

            active_rows = []

            for row in group_rows:

                if row.get(
                    "skipped",
                    False,
                ):
                    skipped_rows += 1

                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "SKIPPED",
                            "reason":
                                "ALREADY_EXISTS",
                        }
                    )

                    continue

                active_rows.append(row)

            if not active_rows:
                continue

            try:
                entity = (
                    cls._import_sales_order_group(
                        organization=organization,
                        created_by=created_by,
                        rows=active_rows,
                    )
                )

                #
                # Batch counters in the migration
                # subsystem represent source rows,
                # not created parent documents.
                #
                imported_rows += len(
                    active_rows
                )

                for row in active_rows:
                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "IMPORTED",
                            "id":
                                str(entity.id),
                            "so_number":
                                so_number,
                        }
                    )

            except Exception as exc:

                failed_rows += len(
                    active_rows
                )

                for row in active_rows:
                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "FAILED",
                            "so_number":
                                so_number,
                            "error":
                                str(exc),
                        }
                    )

        return {
            "imported_rows":
                imported_rows,
            "skipped_rows":
                skipped_rows,
            "failed_rows":
                failed_rows,
            "rows":
                row_results,
        }

    @classmethod
    def _import_goods_receipt_group(
        cls,
        *,
        organization,
        created_by,
        rows,
    ):
        if not rows:
            raise MigrationImportError(
                "Goods receipt group is empty."
            )

        first_normalized = (
            rows[0].get("normalized")
            or {}
        )

        purchase_order_number = str(
            first_normalized.get(
                "purchase_order_number",
                "",
            )
            or ""
        ).strip().upper()

        warehouse_code = str(
            first_normalized.get(
                "warehouse_code",
                "",
            )
            or ""
        ).strip().upper()

        if not purchase_order_number:
            raise MigrationImportError(
                "Validated purchase order number "
                "is unavailable."
            )

        if not warehouse_code:
            raise MigrationImportError(
                "Validated warehouse code "
                "is unavailable."
            )

        # ==============================================
        # RESOLVE PURCHASE ORDER
        # ==============================================

        purchase_order = (
            PurchaseOrderRepository
            .get_by_po_number(
                organization=organization,
                po_number=purchase_order_number,
            )
        )

        if purchase_order is None:
            raise MigrationImportError(
                "Purchase order was not found."
            )

        # ==============================================
        # RESOLVE WAREHOUSE
        # ==============================================

        warehouse = (
            WarehouseRepository
            .get_by_code(
                organization=organization,
                code=warehouse_code,
            )
        )

        if warehouse is None:
            raise MigrationImportError(
                "Warehouse was not found."
            )

        # ==============================================
        # BUILD RECEIPT ITEMS
        # ==============================================

        raw_items = []

        notes = ""

        for row in rows:
            normalized = (
                row.get("normalized")
                or {}
            )

            row_po_number = str(
                normalized.get(
                    "purchase_order_number",
                    "",
                )
                or ""
            ).strip().upper()

            row_warehouse_code = str(
                normalized.get(
                    "warehouse_code",
                    "",
                )
                or ""
            ).strip().upper()

            if (
                row_po_number
                != purchase_order_number
            ):
                raise MigrationImportError(
                    "Goods receipt group contains "
                    "different purchase orders."
                )

            if (
                row_warehouse_code
                != warehouse_code
            ):
                raise MigrationImportError(
                    "Goods receipt group contains "
                    "different warehouses."
                )

            product_sku = str(
                normalized.get(
                    "product_sku",
                    "",
                )
                or ""
            ).strip().upper()

            if not product_sku:
                raise MigrationImportError(
                    "Validated product SKU "
                    "is unavailable."
                )

            product = (
                ProductRepository
                .get_by_sku(
                    organization=organization,
                    sku=product_sku,
                )
            )

            if product is None:
                raise MigrationImportError(
                    f"Product {product_sku} "
                    "was not found."
                )

            quantity_received = (
                normalized.get(
                    "quantity_received"
                )
            )

            if quantity_received in (
                None,
                "",
            ):
                raise MigrationImportError(
                    "Validated received quantity "
                    "is unavailable."
                )

            raw_items.append(
                {
                    "product": product,
                    "quantity_received":
                        quantity_received,
                }
            )

            row_notes = str(
                normalized.get(
                    "notes",
                    "",
                )
                or ""
            ).strip()

            if row_notes and not notes:
                notes = row_notes

        # ==============================================
        # DOMAIN SERVICE
        # ==============================================

        return (
            GoodsReceiptService
            .receive_goods(
                user=created_by,
                organization=organization,
                purchase_order=purchase_order,
                warehouse=warehouse,
                raw_items=raw_items,
                notes=notes,
            )
        )
    @classmethod
    def _import_goods_receipt_rows(
        cls,
        *,
        organization,
        created_by,
        rows,
    ):
        grouped = {}

        for row in rows:
            normalized = (
                row.get("normalized")
                or {}
            )

            purchase_order_number = str(
                normalized.get(
                    "purchase_order_number",
                    "",
                )
                or ""
            ).strip().upper()

            warehouse_code = str(
                normalized.get(
                    "warehouse_code",
                    "",
                )
                or ""
            ).strip().upper()

            if not purchase_order_number:
                raise MigrationImportError(
                    "Validated purchase order number "
                    "is unavailable."
                )

            if not warehouse_code:
                raise MigrationImportError(
                    "Validated warehouse code "
                    "is unavailable."
                )

            group_key = (
                purchase_order_number,
                warehouse_code,
            )

            grouped.setdefault(
                group_key,
                [],
            ).append(row)

        imported_rows = 0
        skipped_rows = 0
        failed_rows = 0
        row_results = []

        for (
            purchase_order_number,
            warehouse_code,
        ), group_rows in grouped.items():

            active_rows = []

            for row in group_rows:
                if row.get(
                    "skipped",
                    False,
                ):
                    skipped_rows += 1

                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "SKIPPED",
                            "reason":
                                "ALREADY_EXISTS",
                        }
                    )

                    continue

                active_rows.append(row)

            if not active_rows:
                continue

            try:
                entity = (
                    cls._import_goods_receipt_group(
                        organization=organization,
                        created_by=created_by,
                        rows=active_rows,
                    )
                )

                imported_rows += len(
                    active_rows
                )

                for row in active_rows:
                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "IMPORTED",
                            "id":
                                str(entity.id),
                            "grn_number":
                                entity.grn_number,
                            "purchase_order_number":
                                purchase_order_number,
                            "warehouse_code":
                                warehouse_code,
                        }
                    )

            except Exception as exc:
                failed_rows += len(
                    active_rows
                )

                for row in active_rows:
                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "FAILED",
                            "purchase_order_number":
                                purchase_order_number,
                            "warehouse_code":
                                warehouse_code,
                            "error":
                                str(exc),
                        }
                    )

        return {
            "imported_rows":
                imported_rows,
            "skipped_rows":
                skipped_rows,
            "failed_rows":
                failed_rows,
            "rows":
                row_results,
        }
    @classmethod
    def _import_purchase_order_rows(
        cls,
        *,
        organization,
        created_by,
        rows,
    ):
        grouped = {}

        for row in rows:
            normalized = row.get(
                "normalized",
                {},
            )

            po_number = str(
                normalized.get(
                    "po_number",
                    "",
                )
                or
                ""
            ).strip().upper()

            if not po_number:
                raise MigrationImportError(
                    "Validated purchase order number "
                    "is unavailable."
                )

            grouped.setdefault(
                po_number,
                [],
            ).append(row)

        imported_rows = 0
        skipped_rows = 0
        failed_rows = 0
        row_results = []

        for po_number, group_rows in grouped.items():

            active_rows = []

            for row in group_rows:
                if row.get(
                    "skipped",
                    False,
                ):
                    skipped_rows += 1

                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "SKIPPED",
                            "reason":
                                "ALREADY_EXISTS",
                        }
                    )

                    continue

                active_rows.append(row)

            if not active_rows:
                continue

            try:
                entity = (
                    cls._import_purchase_order_group(
                        organization=organization,
                        created_by=created_by,
                        rows=active_rows,
                    )
                )

                imported_rows += len(
                    active_rows
                )

                for row in active_rows:
                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "IMPORTED",
                            "id":
                                str(entity.id),
                            "po_number":
                                po_number,
                        }
                    )

            except Exception as exc:
                failed_rows += len(
                    active_rows
                )

                for row in active_rows:
                    row_results.append(
                        {
                            "row_number":
                                row["row_number"],
                            "status":
                                "FAILED",
                            "po_number":
                                po_number,
                            "error":
                                str(exc),
                        }
                    )

        return {
            "imported_rows":
                imported_rows,
            "skipped_rows":
                skipped_rows,
            "failed_rows":
                failed_rows,
            "rows":
                row_results,
        }

    # ==================================================
    # PUBLIC API
    # ==================================================

    @classmethod

    def import_batch(

        cls,

        *,

        organization,

        batch,

    ):

        if organization is None:

            raise MigrationImportError(

                "Organization is required."

            )



        if batch is None:

            raise MigrationImportError(

                "Migration batch is required."

            )



        batch_organization_id = str(

            getattr(

                getattr(

                    batch,

                    "organization",

                    None,

                ),

                "id",

                "",

            )

        )



        organization_id = str(

            getattr(

                organization,

                "id",

                "",

            )

        )



        if (

            not batch_organization_id

            or batch_organization_id

            != organization_id

        ):

            raise MigrationImportError(

                "Migration batch does not "

                "belong to this organization."

            )



        migration_type = str(

            getattr(

                batch,

                "migration_type",

                "",

            )

            or

            ""

        ).strip().upper()



        if (

            migration_type

            not in cls.SUPPORTED_TYPES

        ):

            raise MigrationImportError(

                "Import is not available for "

                "this migration type."

            )



        # ==============================================

        # IMPORT ACTOR

        # ==============================================



        user = getattr(batch, "created_by", None)



        if migration_type in {
            "INVENTORY",
            "SALES_ORDERS",
            "PURCHASE_ORDERS",
            "SALES_INVOICES",
            "GOODS_RECEIPTS",
        }:
            user = getattr(
                batch,
                "created_by",
                None,
            )

            if user is None:
                raise MigrationImportError(
                    "Migration batch does not "
                    "have an import user."
                )



        rows = cls._get_validated_rows(

            batch=batch,

        )



        try:

            (

                MigrationBatchService

                .start_import(

                    batch=batch,

                )

            )

        except ValueError as exc:

            raise MigrationImportError(

                str(exc)

            ) from exc


        imported_rows = 0
        skipped_rows = 0
        failed_rows = 0

        row_results = []

        # ==============================================
        # GROUPED SALES ORDER IMPORT
        # ==============================================

        if migration_type == "SALES_ORDERS":

            grouped_result = (
                cls._import_sales_order_rows(
                    organization=organization,
                    created_by=user,
                    rows=rows,
                )
            )

            imported_rows = grouped_result[
                "imported_rows"
            ]

            skipped_rows = grouped_result[
                "skipped_rows"
            ]

            failed_rows = grouped_result[
                "failed_rows"
            ]

            row_results = grouped_result[
                "rows"
            ]

        elif migration_type == "PURCHASE_ORDERS":

            grouped_result = (
                cls._import_purchase_order_rows(
                    organization=organization,
                    created_by=user,
                    rows=rows,
                )
            )

            imported_rows = grouped_result[
                "imported_rows"
            ]

            skipped_rows = grouped_result[
                "skipped_rows"
            ]

            failed_rows = grouped_result[
                "failed_rows"
            ]

            row_results = grouped_result[
                "rows"
            ]
        elif migration_type == "GOODS_RECEIPTS":

            grouped_result = (
                cls._import_goods_receipt_rows(
                    organization=organization,
                    created_by=user,
                    rows=rows,
                )
            )

            imported_rows = grouped_result[
                "imported_rows"
            ]

            skipped_rows = grouped_result[
                "skipped_rows"
            ]

            failed_rows = grouped_result[
                "failed_rows"
            ]

            row_results = grouped_result[
                "rows"
            ]
        else:

            for row in rows:

                row_number = row[
                    "row_number"
                ]

                normalized = row[
                    "normalized"
                ]

                if row.get(
                    "skipped",
                    False,
                ):

                    skipped_rows += 1

                    row_results.append(
                        {
                            "row_number":
                                row_number,
                            "status":
                                "SKIPPED",
                            "reason":
                                "ALREADY_EXISTS",
                        }
                    )

                    continue

                try:

                    entity = cls._import_row(
                        user=user,
                        organization=organization,
                        migration_type=(
                            migration_type
                        ),
                        normalized=normalized,
                    )

                    imported_rows += 1

                    row_results.append(
                        {
                            "row_number":
                                row_number,
                            "status":
                                "IMPORTED",
                            "id":
                                str(
                                    entity.id
                                ),
                        }
                    )

                except Exception as exc:

                    failed_rows += 1

                    row_results.append(
                        {
                            "row_number":
                                row_number,
                            "status":
                                "FAILED",
                            "error":
                                str(exc),
                        }
                    )

        import_result = {

            "migration_type":

                migration_type,

            "imported_rows":

                imported_rows,

            "skipped_rows":

                skipped_rows,

            "failed_rows":

                failed_rows,

            "rows":

                row_results,

        }

        try:
            batch = (
                MigrationBatchService.complete_import(
                    batch=batch,
                    imported_rows=imported_rows,
                    skipped_rows=skipped_rows,
                    failed_rows=failed_rows,
                    import_result={
                        "migration_type":
                            migration_type,
                        "imported_rows":
                            imported_rows,
                        "skipped_rows":
                            skipped_rows,
                        "failed_rows":
                            failed_rows,
                        "rows":
                            row_results,
                    },
                )

            )



        except Exception as exc:

            try:

                (

                    MigrationBatchService

                    .fail_import(

                        batch=batch,

                        error_summary=str(exc),

                    )

                )



            except Exception:

                pass



            raise MigrationImportError(

                str(exc)

                or

                "Migration import failed."

            ) from exc



        return {

            "batch": batch,

            "import": import_result,

        }
