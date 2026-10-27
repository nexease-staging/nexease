from decimal import (
    Decimal,
    InvalidOperation,
)
from datetime import (
    date,
    datetime,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.products.repositories.category_repository import (
    CategoryRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
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
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)


class MigrationRowValidationError(
    ValueError,
):
    pass


class MigrationRowValidationService:

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

    # ==================================================
    # COMMON HELPERS
    # ==================================================

    @staticmethod
    def _string(
        value,
    ):
        if value is None:
            return ""

        return str(value).strip()

    @classmethod
    def _add_error(
        cls,
        errors,
        *,
        field,
        code,
        message,
    ):
        errors.append(
            {
                "field": field,
                "code": code,
                "message": message,
            }
        )

    @classmethod
    def _required_string(
        cls,
        value,
        *,
        field,
        maximum_length,
        errors,
    ):
        value = cls._string(
            value
        )

        if not value:
            cls._add_error(
                errors,
                field=field,
                code="REQUIRED",
                message=(
                    f"{field} is required."
                ),
            )

            return ""

        if len(value) > maximum_length:
            cls._add_error(
                errors,
                field=field,
                code="MAX_LENGTH",
                message=(
                    f"{field} cannot exceed "
                    f"{maximum_length} characters."
                ),
            )

        return value

    @classmethod
    def _date(
        cls,
        value,
        *,
        field,
        errors,
        required=True,
    ):
        if value is None or value == "":
            if required:
                cls._add_error(
                    errors,
                    field=field,
                    code="REQUIRED",
                    message=f"{field} is required.",
                )
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text = str(value).strip()

        formats = (
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        )

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                ).date()
            except ValueError:
                continue

        cls._add_error(
            errors,
            field=field,
            code="INVALID_DATE",
            message=(
                f"{field} must be a valid date. "
                "Supported formats include "
                "YYYY-MM-DD, DD-MM-YYYY and DD/MM/YYYY."
            ),
        )

        return None

    @classmethod
    def _positive_quantity(
        cls,
        value,
        *,
        field,
        errors,
    ):
        quantity = cls._price(
            value,
            field=field,
            errors=errors,
        )

        if quantity is None:
            return None

        if quantity <= 0:
            cls._add_error(
                errors,
                field=field,
                code="INVALID_QUANTITY",
                message=(
                    f"{field} must be greater than zero."
                ),
            )

            return None

        return quantity

    @classmethod
    def _optional_string(
        cls,
        value,
        *,
        field,
        maximum_length,
        errors,
    ):
        value = cls._string(
            value
        )

        if len(value) > maximum_length:
            cls._add_error(
                errors,
                field=field,
                code="MAX_LENGTH",
                message=(
                    f"{field} cannot exceed "
                    f"{maximum_length} characters."
                ),
            )

        return value

    @classmethod
    def _price(
        cls,
        value,
        *,
        field,
        errors,
    ):
        if (
            value is None
            or
            cls._string(value) == ""
        ):
            return Decimal("0.00")

        if isinstance(
            value,
            bool,
        ):
            cls._add_error(
                errors,
                field=field,
                code="INVALID_DECIMAL",
                message=(
                    f"{field} must be "
                    "a valid number."
                ),
            )

            return None

        try:
            price = Decimal(
                str(value).strip()
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            cls._add_error(
                errors,
                field=field,
                code="INVALID_DECIMAL",
                message=(
                    f"{field} must be "
                    "a valid number."
                ),
            )

            return None

        if not price.is_finite():
            cls._add_error(
                errors,
                field=field,
                code="INVALID_DECIMAL",
                message=(
                    f"{field} must be "
                    "a finite number."
                ),
            )

            return None

        if price < Decimal("0"):
            cls._add_error(
                errors,
                field=field,
                code="NEGATIVE_VALUE",
                message=(
                    f"{field} cannot "
                    "be negative."
                ),
            )

        decimal_places = (
            -price.as_tuple().exponent
            if price.as_tuple().exponent < 0
            else 0
        )

        if decimal_places > 2:
            cls._add_error(
                errors,
                field=field,
                code="DECIMAL_PLACES",
                message=(
                    f"{field} cannot have "
                    "more than 2 decimal places."
                ),
            )

        if errors:
            field_has_error = any(
                error["field"] == field
                for error in errors
            )

            if field_has_error:
                return None

        return price.quantize(
            Decimal("0.01")
        )

    # ==================================================
    # CATEGORY
    # ==================================================

    @classmethod
    def _validate_category_row(
        cls,
        *,
        organization,
        row,
        seen_category_names,
    ):
        errors = []

        name = cls._required_string(
            row.get("name"),
            field="name",
            maximum_length=100,
            errors=errors,
        )

        description = cls._optional_string(
            row.get(
                "description",
                "",
            ),
            field="description",
            maximum_length=500,
            errors=errors,
        )

        normalized_name = (
            name.casefold()
            if name
            else ""
        )

        if normalized_name:
            if (
                normalized_name
                in seen_category_names
            ):
                cls._add_error(
                    errors,
                    field="name",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "Category name is "
                        "duplicated in the "
                        "migration file."
                    ),
                )
            else:
                seen_category_names.add(
                    normalized_name
                )

            existing = (
                CategoryRepository
                .get_by_name(
                    organization=organization,
                    name=name,
                )
            )

            if existing:
                cls._add_error(
                    errors,
                    field="name",
                    code="ALREADY_EXISTS",
                    message=(
                        "A category with this "
                        "name already exists."
                    ),
                )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "name": name,
                "description": description,
            },
        }

    # ==================================================
    # PRODUCT
    # ==================================================

    @classmethod
    def _validate_product_row(
        cls,
        *,
        organization,
        row,
        seen_skus,
    ):
        errors = []

        sku = cls._required_string(
            row.get("sku"),
            field="sku",
            maximum_length=50,
            errors=errors,
        ).upper()

        name = cls._required_string(
            row.get("name"),
            field="name",
            maximum_length=200,
            errors=errors,
        )

        category_name = (
            cls._required_string(
                row.get("category"),
                field="category",
                maximum_length=100,
                errors=errors,
            )
        )

        unit = cls._required_string(
            row.get("unit"),
            field="unit",
            maximum_length=30,
            errors=errors,
        )

        description = cls._optional_string(
            row.get(
                "description",
                "",
            ),
            field="description",
            maximum_length=1000,
            errors=errors,
        )

        brand = cls._optional_string(
            row.get(
                "brand",
                "",
            ),
            field="brand",
            maximum_length=100,
            errors=errors,
        )

        barcode = cls._optional_string(
            row.get(
                "barcode",
                "",
            ),
            field="barcode",
            maximum_length=100,
            errors=errors,
        )

        cost_price = cls._price(
            row.get(
                "cost_price",
                0,
            ),
            field="cost_price",
            errors=errors,
        )

        selling_price = cls._price(
            row.get(
                "selling_price",
                0,
            ),
            field="selling_price",
            errors=errors,
        )

        # ==============================================
        # SKU UNIQUENESS
        # ==============================================

        if sku:
            if sku in seen_skus:
                cls._add_error(
                    errors,
                    field="sku",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "SKU is duplicated in "
                        "the migration file."
                    ),
                )
            else:
                seen_skus.add(
                    sku
                )

            if (
                ProductRepository
                .sku_exists(
                    organization=organization,
                    sku=sku,
                )
            ):
                cls._add_error(
                    errors,
                    field="sku",
                    code="ALREADY_EXISTS",
                    message=(
                        "A product with this "
                        "SKU already exists."
                    ),
                )

        # ==============================================
        # CATEGORY RESOLUTION
        # ==============================================

        category = None

        if category_name:
            category = (
                CategoryRepository
                .get_active_by_name(
                    organization=organization,
                    name=category_name,
                )
            )

            if not category:
                cls._add_error(
                    errors,
                    field="category",
                    code="CATEGORY_NOT_FOUND",
                    message=(
                        "Active category was "
                        "not found in the "
                        "current organization."
                    ),
                )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "sku": sku,
                "name": name,
                "description": description,
                "category": category,
                "category_name":
                    category_name,
                "brand": brand,
                "unit": unit,
                "cost_price":
                    cost_price,
                "selling_price":
                    selling_price,
                "barcode": barcode,
            },
        }

    # ==================================================
    # CUSTOMER
    # ==================================================

    @classmethod
    def _validate_customer_row(
        cls,
        *,
        organization,
        row,
        seen_customer_codes,
    ):
        errors = []

        code = (
            cls._required_string(
                row.get("code"),
                field="code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        name = cls._required_string(
            row.get("name"),
            field="name",
            maximum_length=200,
            errors=errors,
        )

        email = cls._optional_string(
            row.get(
                "email",
                "",
            ),
            field="email",
            maximum_length=254,
            errors=errors,
        ).lower()

        phone = cls._optional_string(
            row.get(
                "phone",
                "",
            ),
            field="phone",
            maximum_length=30,
            errors=errors,
        )

        gstin = (
            cls._optional_string(
                row.get(
                    "gstin",
                    "",
                ),
                field="gstin",
                maximum_length=20,
                errors=errors,
            )
            .upper()
        )

        billing_address = (
            cls._optional_string(
                row.get(
                    "billing_address",
                    "",
                ),
                field="billing_address",
                maximum_length=500,
                errors=errors,
            )
        )

        shipping_address = (
            cls._optional_string(
                row.get(
                    "shipping_address",
                    "",
                ),
                field="shipping_address",
                maximum_length=500,
                errors=errors,
            )
        )

        city = cls._optional_string(
            row.get(
                "city",
                "",
            ),
            field="city",
            maximum_length=100,
            errors=errors,
        )

        state = cls._optional_string(
            row.get(
                "state",
                "",
            ),
            field="state",
            maximum_length=100,
            errors=errors,
        )

        country = cls._optional_string(
            row.get(
                "country",
                "India",
            ),
            field="country",
            maximum_length=100,
            errors=errors,
        )

        if not country:
            country = "India"

        pincode = cls._optional_string(
            row.get(
                "pincode",
                "",
            ),
            field="pincode",
            maximum_length=20,
            errors=errors,
        )

        # ==============================================
        # CUSTOMER CODE UNIQUENESS
        # ==============================================

        if code:
            if code in seen_customer_codes:
                cls._add_error(
                    errors,
                    field="code",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "Customer code is duplicated "
                        "in the migration file."
                    ),
                )
            else:
                seen_customer_codes.add(
                    code
                )

            if (
                CustomerRepository
                .code_exists(
                    organization=organization,
                    code=code,
                )
            ):
                cls._add_error(
                    errors,
                    field="code",
                    code="ALREADY_EXISTS",
                    message=(
                        "A customer with this "
                        "code already exists."
                    ),
                )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "code": code,
                "name": name,
                "email": email,
                "phone": phone,
                "gstin": gstin,
                "billing_address":
                    billing_address,
                "shipping_address":
                    shipping_address,
                "city": city,
                "state": state,
                "country": country,
                "pincode": pincode,
            },
        }

    # ==================================================
    # SUPPLIER
    # ==================================================

    @classmethod
    def _validate_supplier_row(
        cls,
        *,
        organization,
        row,
        seen_supplier_codes,
    ):
        errors = []

        code = (
            cls._required_string(
                row.get("code"),
                field="code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        name = cls._required_string(
            row.get("name"),
            field="name",
            maximum_length=200,
            errors=errors,
        )

        email = cls._optional_string(
            row.get(
                "email",
                "",
            ),
            field="email",
            maximum_length=254,
            errors=errors,
        ).lower()

        phone = cls._optional_string(
            row.get(
                "phone",
                "",
            ),
            field="phone",
            maximum_length=30,
            errors=errors,
        )

        gstin = (
            cls._optional_string(
                row.get(
                    "gstin",
                    "",
                ),
                field="gstin",
                maximum_length=20,
                errors=errors,
            )
            .upper()
        )

        address = cls._optional_string(
            row.get(
                "address",
                "",
            ),
            field="address",
            maximum_length=500,
            errors=errors,
        )

        city = cls._optional_string(
            row.get(
                "city",
                "",
            ),
            field="city",
            maximum_length=100,
            errors=errors,
        )

        state = cls._optional_string(
            row.get(
                "state",
                "",
            ),
            field="state",
            maximum_length=100,
            errors=errors,
        )

        country = cls._optional_string(
            row.get(
                "country",
                "India",
            ),
            field="country",
            maximum_length=100,
            errors=errors,
        )

        if not country:
            country = "India"

        pincode = cls._optional_string(
            row.get(
                "pincode",
                "",
            ),
            field="pincode",
            maximum_length=20,
            errors=errors,
        )

        # ==============================================
        # SUPPLIER CODE UNIQUENESS
        # ==============================================

        if code:
            if code in seen_supplier_codes:
                cls._add_error(
                    errors,
                    field="code",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "Supplier code is duplicated "
                        "in the migration file."
                    ),
                )
            else:
                seen_supplier_codes.add(
                    code
                )

            if (
                SupplierRepository
                .code_exists(
                    organization=organization,
                    code=code,
                )
            ):
                cls._add_error(
                    errors,
                    field="code",
                    code="ALREADY_EXISTS",
                    message=(
                        "A supplier with this "
                        "code already exists."
                    ),
                )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "code": code,
                "name": name,
                "email": email,
                "phone": phone,
                "gstin": gstin,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "pincode": pincode,
            },
        }

    # ==================================================
    # WAREHOUSE
    # ==================================================

    @classmethod
    def _validate_warehouse_row(
        cls,
        *,
        organization,
        row,
        seen_warehouse_codes,
        seen_warehouse_names,
    ):
        errors = []

        code = (
            cls._required_string(
                row.get("code"),
                field="code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        name = cls._required_string(
            row.get("name"),
            field="name",
            maximum_length=200,
            errors=errors,
        )

        address = cls._optional_string(
            row.get(
                "address",
                "",
            ),
            field="address",
            maximum_length=500,
            errors=errors,
        )

        city = cls._optional_string(
            row.get(
                "city",
                "",
            ),
            field="city",
            maximum_length=100,
            errors=errors,
        )

        state = cls._optional_string(
            row.get(
                "state",
                "",
            ),
            field="state",
            maximum_length=100,
            errors=errors,
        )

        country = cls._optional_string(
            row.get(
                "country",
                "India",
            ),
            field="country",
            maximum_length=100,
            errors=errors,
        )

        if not country:
            country = "India"

        pincode = cls._optional_string(
            row.get(
                "pincode",
                "",
            ),
            field="pincode",
            maximum_length=20,
            errors=errors,
        )

        # ==============================================
        # WAREHOUSE CODE UNIQUENESS
        # ==============================================

        if code:
            if code in seen_warehouse_codes:
                cls._add_error(
                    errors,
                    field="code",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "Warehouse code is duplicated "
                        "in the migration file."
                    ),
                )
            else:
                seen_warehouse_codes.add(
                    code
                )

            if (
                WarehouseRepository
                .code_exists(
                    organization=organization,
                    code=code,
                )
            ):
                cls._add_error(
                    errors,
                    field="code",
                    code="ALREADY_EXISTS",
                    message=(
                        "A warehouse with this "
                        "code already exists."
                    ),
                )

        # ==============================================
        # WAREHOUSE NAME UNIQUENESS
        # ==============================================

        if name:
            normalized_name_key = (
                name.casefold()
            )

            if (
                normalized_name_key
                in seen_warehouse_names
            ):
                cls._add_error(
                    errors,
                    field="name",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "Warehouse name is duplicated "
                        "in the migration file."
                    ),
                )
            else:
                seen_warehouse_names.add(
                    normalized_name_key
                )

            if (
                WarehouseRepository
                .name_exists(
                    organization=organization,
                    name=name,
                )
            ):
                cls._add_error(
                    errors,
                    field="name",
                    code="ALREADY_EXISTS",
                    message=(
                        "A warehouse with this "
                        "name already exists."
                    ),
                )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "code": code,
                "name": name,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "pincode": pincode,
            },
        }

    # ==================================================
    # INVENTORY
    # ==================================================

    @classmethod
    def _validate_inventory_row(
        cls,
        *,
        organization,
        row,
        seen_inventory_keys,
    ):
        errors = []

        product_sku = (
            cls._required_string(
                row.get("product_sku"),
                field="product_sku",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        warehouse_code = (
            cls._required_string(
                row.get("warehouse_code"),
                field="warehouse_code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        quantity = cls._price(
            row.get("quantity"),
            field="quantity",
            errors=errors,
        )

        # ==============================================
        # PRODUCT RESOLUTION
        # ==============================================

        product = None

        if product_sku:
            product = (
                ProductRepository
                .get_by_sku(
                    organization=organization,
                    sku=product_sku,
                )
            )

            if not product:
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_NOT_FOUND",
                    message=(
                        "Product was not found in "
                        "the current organization."
                    ),
                )

        # ==============================================
        # WAREHOUSE RESOLUTION
        # ==============================================

        warehouse = None

        if warehouse_code:
            warehouse = (
                WarehouseRepository
                .get_by_code(
                    organization=organization,
                    code=warehouse_code,
                )
            )

            if not warehouse:
                cls._add_error(
                    errors,
                    field="warehouse_code",
                    code="WAREHOUSE_NOT_FOUND",
                    message=(
                        "Warehouse was not found in "
                        "the current organization."
                    ),
                )
        # ==============================================
        # EXISTING INVENTORY
        # ==============================================

        if (
            product is not None
            and warehouse is not None
            and InventoryRepository
            .exists_for_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=warehouse,
            )
        ):
            cls._add_error(
                errors,
                field="product_sku",
                code="ALREADY_EXISTS",
                message=(
                    "Inventory already exists for "
                    "this product and warehouse."
                ),
            )
        # ==============================================
        # DUPLICATE PRODUCT / WAREHOUSE
        # ==============================================

        if product_sku and warehouse_code:
            inventory_key = (
                product_sku,
                warehouse_code,
            )

            if inventory_key in seen_inventory_keys:
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "The product and warehouse "
                        "combination is duplicated "
                        "in the migration file."
                    ),
                )
            else:
                seen_inventory_keys.add(
                    inventory_key
                )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "product_sku": product_sku,
                "product": product,
                "warehouse_code": warehouse_code,
                "warehouse": warehouse,
                "quantity": quantity,
            },
        }

    # ==================================================
    # SALES ORDERS
    # ==================================================

    @classmethod
    def _validate_sales_order_row(
        cls,
        *,
        organization,
        row,
        seen_sales_order_lines,
    ):
        errors = []

        # ==============================================
        # BASIC FIELDS
        # ==============================================

        so_number = (
            cls._required_string(
                row.get("so_number"),
                field="so_number",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        customer_code = (
            cls._required_string(
                row.get("customer_code"),
                field="customer_code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        product_sku = (
            cls._required_string(
                row.get("product_sku"),
                field="product_sku",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        warehouse_code = (
            cls._required_string(
                row.get("warehouse_code"),
                field="warehouse_code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        order_date = cls._date(
            row.get("order_date"),
            field="order_date",
            errors=errors,
        )

        expected_delivery_date = cls._date(
            row.get("expected_delivery_date"),
            field="expected_delivery_date",
            errors=errors,
            required=False,
        )

        quantity = cls._positive_quantity(
            row.get("quantity"),
            field="quantity",
            errors=errors,
        )

        unit_price = cls._price(
            row.get("unit_price"),
            field="unit_price",
            errors=errors,
        )
        tax_rate = cls._price(
            row.get("tax_rate") or 0,
            field="tax_rate",
            errors=errors,
        )

        discount = cls._price(
            row.get("discount") or 0,
            field="discount",
            errors=errors,
        )

        notes = str(
            row.get("notes") or ""
        ).strip()

        if (
            tax_rate is not None
            and tax_rate < 0
        ):
            cls._add_error(
                errors,
                field="tax_rate",
                code="INVALID_TAX_RATE",
                message=(
                    "tax_rate cannot be negative."
                ),
            )

        if (
            discount is not None
            and discount < 0
        ):
            cls._add_error(
                errors,
                field="discount",
                code="INVALID_DISCOUNT",
                message=(
                    "discount cannot be negative."
                ),
            )

        if (
            quantity is not None
            and unit_price is not None
            and discount is not None
        ):
            line_subtotal = (
                quantity * unit_price
            )

            if discount > line_subtotal:
                cls._add_error(
                    errors,
                    field="discount",
                    code="INVALID_DISCOUNT",
                    message=(
                        "Discount cannot exceed "
                        "the line subtotal."
                    ),
                )
        # ==============================================
        # PRICE VALIDATION
        # ==============================================

        if (
            unit_price is not None
            and unit_price < 0
        ):
            cls._add_error(
                errors,
                field="unit_price",
                code="INVALID_PRICE",
                message=(
                    "unit_price cannot be negative."
                ),
            )

        # ==============================================
        # DATE VALIDATION
        # ==============================================

        if (
            order_date is not None
            and expected_delivery_date is not None
            and expected_delivery_date < order_date
        ):
            cls._add_error(
                errors,
                field="expected_delivery_date",
                code="INVALID_DELIVERY_DATE",
                message=(
                    "Expected delivery date cannot be "
                    "before the order date."
                ),
            )

        # ==============================================
        # CUSTOMER RESOLUTION
        # ==============================================

        customer = None

        if customer_code:
            customer = (
                CustomerRepository
                .get_by_code(
                    organization=organization,
                    code=customer_code,
                )
            )

            if not customer:
                cls._add_error(
                    errors,
                    field="customer_code",
                    code="CUSTOMER_NOT_FOUND",
                    message=(
                        "Customer was not found in "
                        "the current organization."
                    ),
                )

            elif not getattr(
                customer,
                "is_active",
                True,
            ):
                cls._add_error(
                    errors,
                    field="customer_code",
                    code="CUSTOMER_INACTIVE",
                    message=(
                        "Customer is inactive."
                    ),
                )

        # ==============================================
        # PRODUCT RESOLUTION
        # ==============================================

        product = None

        if product_sku:
            product = (
                ProductRepository
                .get_by_sku(
                    organization=organization,
                    sku=product_sku,
                )
            )

            if not product:
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_NOT_FOUND",
                    message=(
                        "Product was not found in "
                        "the current organization."
                    ),
                )

            elif not getattr(
                product,
                "is_active",
                True,
            ):
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_INACTIVE",
                    message=(
                        "Product is inactive."
                    ),
                )

        # ==============================================
        # WAREHOUSE RESOLUTION
        # ==============================================

        warehouse = None

        if warehouse_code:
            warehouse = (
                WarehouseRepository
                .get_by_code(
                    organization=organization,
                    code=warehouse_code,
                )
            )

            if not warehouse:
                cls._add_error(
                    errors,
                    field="warehouse_code",
                    code="WAREHOUSE_NOT_FOUND",
                    message=(
                        "Warehouse was not found in "
                        "the current organization."
                    ),
                )

            elif not getattr(
                warehouse,
                "is_active",
                True,
            ):
                cls._add_error(
                    errors,
                    field="warehouse_code",
                    code="WAREHOUSE_INACTIVE",
                    message=(
                        "Warehouse is inactive."
                    ),
                )

        # ==============================================
        # EXISTING SALES ORDER
        # ==============================================

        if so_number:
            existing_order = (
                SalesOrderRepository
                .get_by_so_number(
                    organization=organization,
                    so_number=so_number,
                )
            )

            if existing_order:
                cls._add_error(
                    errors,
                    field="so_number",
                    code="ALREADY_EXISTS",
                    message=(
                        "A sales order with this "
                        "SO number already exists."
                    ),
                )

        # ==============================================
        # DUPLICATE SO LINE IN MIGRATION FILE
        # ==============================================

        if so_number and product_sku:
            line_key = (
                so_number,
                product_sku,
            )

            if line_key in seen_sales_order_lines:
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "This product is duplicated "
                        "within the same sales order."
                    ),
                )
            else:
                seen_sales_order_lines.add(
                    line_key
                )

        # ==============================================
        # NORMALIZED RESULT
        # ==============================================

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "so_number": so_number,
                "customer_code": customer_code,
                "customer_id": (
                    str(customer.id)
                    if customer is not None
                    else None
                ),
                "product_sku": product_sku,
                "product_id": (
                    str(product.id)
                    if product is not None
                    else None
                ),
                "warehouse_code": warehouse_code,
                "warehouse_id": (
                    str(warehouse.id)
                    if warehouse is not None
                    else None
                ),
                "order_date": (
                    order_date.isoformat()
                    if order_date is not None
                    else None
                ),
                "expected_delivery_date": (
                    expected_delivery_date.isoformat()
                    if expected_delivery_date is not None
                    else None
                ),
                "quantity": (
                    str(quantity)
                    if quantity is not None
                    else None
                ),
                "unit_price": (
                    str(unit_price)
                    if unit_price is not None
                    else None
                ),
                "tax_rate": (
                    str(tax_rate)
                    if tax_rate is not None
                    else None
                ),
                "discount": (
                    str(discount)
                    if discount is not None
                    else None
                ),
                "notes": notes,
            },
        }

    # ==================================================
    # PURCHASE ORDERS
    # ==================================================

    @classmethod
    def _validate_purchase_order_row(
        cls,
        *,
        organization,
        row,
        seen_purchase_order_lines,
    ):
        errors = []

        # ==============================================
        # BASIC FIELDS
        # ==============================================

        po_number = (
            cls._required_string(
                row.get("po_number"),
                field="po_number",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        supplier_code = (
            cls._required_string(
                row.get("supplier_code"),
                field="supplier_code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        product_sku = (
            cls._required_string(
                row.get("product_sku"),
                field="product_sku",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        order_date = cls._date(
            row.get("order_date"),
            field="order_date",
            errors=errors,
        )

        expected_delivery_date = cls._date(
            row.get(
                "expected_delivery_date"
            ),
            field="expected_delivery_date",
            errors=errors,
            required=False,
        )

        quantity = cls._positive_quantity(
            row.get("quantity"),
            field="quantity",
            errors=errors,
        )

        unit_price = cls._price(
            row.get("unit_price"),
            field="unit_price",
            errors=errors,
        )

        tax_rate = cls._price(
            row.get("tax_rate") or 0,
            field="tax_rate",
            errors=errors,
        )

        discount = cls._price(
            row.get("discount") or 0,
            field="discount",
            errors=errors,
        )

        notes = str(
            row.get("notes") or ""
        ).strip()

        # ==============================================
        # AMOUNT VALIDATION
        # ==============================================

        if (
            unit_price is not None
            and unit_price < 0
        ):
            cls._add_error(
                errors,
                field="unit_price",
                code="INVALID_PRICE",
                message=(
                    "unit_price cannot be negative."
                ),
            )

        if (
            tax_rate is not None
            and tax_rate < 0
        ):
            cls._add_error(
                errors,
                field="tax_rate",
                code="INVALID_TAX_RATE",
                message=(
                    "tax_rate cannot be negative."
                ),
            )

        if (
            discount is not None
            and discount < 0
        ):
            cls._add_error(
                errors,
                field="discount",
                code="INVALID_DISCOUNT",
                message=(
                    "discount cannot be negative."
                ),
            )

        if (
            quantity is not None
            and unit_price is not None
            and discount is not None
        ):
            line_value = (
                quantity
                * unit_price
            )

            if discount > line_value:
                cls._add_error(
                    errors,
                    field="discount",
                    code="INVALID_DISCOUNT",
                    message=(
                        "Discount cannot exceed "
                        "the line value."
                    ),
                )

        # ==============================================
        # DATE VALIDATION
        # ==============================================

        if (
            order_date is not None
            and expected_delivery_date
            is not None
            and expected_delivery_date
            < order_date
        ):
            cls._add_error(
                errors,
                field=(
                    "expected_delivery_date"
                ),
                code="INVALID_DELIVERY_DATE",
                message=(
                    "Expected delivery date "
                    "cannot be before the "
                    "order date."
                ),
            )

        # ==============================================
        # SUPPLIER RESOLUTION
        # ==============================================

        supplier = None

        if supplier_code:
            supplier = (
                SupplierRepository
                .get_by_code(
                    organization=organization,
                    code=supplier_code,
                )
            )

            if not supplier:
                cls._add_error(
                    errors,
                    field="supplier_code",
                    code="SUPPLIER_NOT_FOUND",
                    message=(
                        "Supplier was not found "
                        "in the current "
                        "organization."
                    ),
                )

            elif not getattr(
                supplier,
                "is_active",
                True,
            ):
                cls._add_error(
                    errors,
                    field="supplier_code",
                    code="SUPPLIER_INACTIVE",
                    message=(
                        "Supplier is inactive."
                    ),
                )

        # ==============================================
        # PRODUCT RESOLUTION
        # ==============================================

        product = None

        if product_sku:
            product = (
                ProductRepository
                .get_by_sku(
                    organization=organization,
                    sku=product_sku,
                )
            )

            if not product:
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_NOT_FOUND",
                    message=(
                        "Product was not found "
                        "in the current "
                        "organization."
                    ),
                )

            elif not getattr(
                product,
                "is_active",
                True,
            ):
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_INACTIVE",
                    message=(
                        "Product is inactive."
                    ),
                )

        # ==============================================
        # EXISTING PURCHASE ORDER
        # ==============================================

        if po_number:
            existing_order = (
                PurchaseOrderRepository
                .get_by_po_number(
                    organization=organization,
                    po_number=po_number,
                )
            )

            if existing_order:
                cls._add_error(
                    errors,
                    field="po_number",
                    code="ALREADY_EXISTS",
                    message=(
                        "A purchase order with "
                        "this PO number already "
                        "exists."
                    ),
                )

        # ==============================================
        # DUPLICATE PO LINE IN MIGRATION FILE
        # ==============================================

        if po_number and product_sku:
            line_key = (
                po_number,
                product_sku,
            )

            if (
                line_key
                in seen_purchase_order_lines
            ):
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "This product is "
                        "duplicated within the "
                        "same purchase order."
                    ),
                )
            else:
                seen_purchase_order_lines.add(
                    line_key
                )

        # ==============================================
        # NORMALIZED RESULT
        # ==============================================

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "po_number": po_number,
                "supplier_code":
                    supplier_code,
                "supplier_id": (
                    str(supplier.id)
                    if supplier is not None
                    else None
                ),
                "product_sku":
                    product_sku,
                "product_id": (
                    str(product.id)
                    if product is not None
                    else None
                ),
                "order_date": (
                    order_date.isoformat()
                    if order_date is not None
                    else None
                ),
                "expected_delivery_date": (
                    expected_delivery_date
                    .isoformat()
                    if expected_delivery_date
                    is not None
                    else None
                ),
                "quantity": (
                    str(quantity)
                    if quantity is not None
                    else None
                ),
                "unit_price": (
                    str(unit_price)
                    if unit_price is not None
                    else None
                ),
                "tax_rate": (
                    str(tax_rate)
                    if tax_rate is not None
                    else None
                ),
                "discount": (
                    str(discount)
                    if discount is not None
                    else None
                ),
                "notes": notes,
            },
        }

    # ==================================================
    # SALES INVOICE
    # ==================================================

    @classmethod
    def _validate_sales_invoice_row(
        cls,
        *,
        organization,
        row,
        seen_invoice_numbers,
        seen_invoice_sales_orders,
    ):
        errors = []

        # ==============================================
        # BASIC FIELDS
        # ==============================================

        invoice_number = (
            cls._required_string(
                row.get("invoice_number"),
                field="invoice_number",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        sales_order_number = (
            cls._required_string(
                row.get("sales_order_number"),
                field="sales_order_number",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        invoice_date = cls._date(
            row.get("invoice_date"),
            field="invoice_date",
            errors=errors,
            required=True,
        )

        due_date = cls._date(
            row.get("due_date"),
            field="due_date",
            errors=errors,
            required=False,
        )

        notes = cls._optional_string(
            row.get(
                "notes",
                "",
            ),
            field="notes",
            maximum_length=1000,
            errors=errors,
        )

        # ==============================================
        # DATE VALIDATION
        # ==============================================

        if (
            invoice_date is not None
            and due_date is not None
            and due_date < invoice_date
        ):
            cls._add_error(
                errors,
                field="due_date",
                code="INVALID_DATE_RANGE",
                message=(
                    "Due date cannot be before "
                    "invoice date."
                ),
            )

        # ==============================================
        # INVOICE NUMBER UNIQUENESS
        # ==============================================

        if invoice_number:

            if (
                invoice_number
                in seen_invoice_numbers
            ):
                cls._add_error(
                    errors,
                    field="invoice_number",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "Invoice number is duplicated "
                        "in the migration file."
                    ),
                )
            else:
                seen_invoice_numbers.add(
                    invoice_number
                )

            existing_invoice = (
                InvoiceRepository
                .get_by_invoice_number(
                    organization=organization,
                    invoice_number=invoice_number,
                )
            )

            if existing_invoice is not None:
                cls._add_error(
                    errors,
                    field="invoice_number",
                    code="ALREADY_EXISTS",
                    message=(
                        "An invoice with this "
                        "invoice number already exists."
                    ),
                )

        # ==============================================
        # SALES ORDER
        # ==============================================

        sales_order = None

        if sales_order_number:

            sales_order = (
                SalesOrderRepository
                .get_by_so_number(
                    organization=organization,
                    so_number=sales_order_number,
                )
            )

            if sales_order is None:
                cls._add_error(
                    errors,
                    field="sales_order_number",
                    code="NOT_FOUND",
                    message=(
                        "Sales order was not found."
                    ),
                )

        # ==============================================
        # ONE INVOICE PER SALES ORDER
        # ==============================================

        if sales_order is not None:

            # ==============================================
            # SALES ORDER STATUS
            # ==============================================

            if (
                sales_order.status
                != "FULFILLED"
            ):
                cls._add_error(
                    errors,
                    field="sales_order_number",
                    code="INVALID_STATUS",
                    message=(
                        "Invoice can only be generated "
                        "from a fulfilled sales order."
                    ),
                )
            sales_order_key = str(
                getattr(
                    sales_order,
                    "id",
                    sales_order_number,
                )
            )

            if (
                sales_order_key
                in seen_invoice_sales_orders
            ):
                cls._add_error(
                    errors,
                    field="sales_order_number",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "Multiple invoices for the same "
                        "sales order are present in the "
                        "migration file."
                    ),
                )
            else:
                seen_invoice_sales_orders.add(
                    sales_order_key
                )

            existing_sales_order_invoice = (
                InvoiceRepository
                .get_by_sales_order(
                    organization=organization,
                    sales_order=sales_order,
                )
            )

            if (
                existing_sales_order_invoice
                is not None
            ):
                cls._add_error(
                    errors,
                    field="sales_order_number",
                    code="ALREADY_EXISTS",
                    message=(
                        "An invoice already exists for "
                        "this sales order."
                    ),
                )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "invoice_number":
                    invoice_number,
                "sales_order_number":
                    sales_order_number,
                "sales_order":
                    sales_order,
                "invoice_date":
                    invoice_date,
                "due_date":
                    due_date,
                "notes":
                    notes,
            },
        }

    # ==================================================
    # GOODS RECEIPT
    # ==================================================

    @classmethod
    def _validate_goods_receipt_row(
        cls,
        *,
        organization,
        row,
        seen_goods_receipt_lines,
    ):
        errors = []

        # ==============================================
        # BASIC FIELDS
        # ==============================================

        purchase_order_number = (
            cls._required_string(
                row.get(
                    "purchase_order_number"
                ),
                field="purchase_order_number",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        warehouse_code = (
            cls._required_string(
                row.get("warehouse_code"),
                field="warehouse_code",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        product_sku = (
            cls._required_string(
                row.get("product_sku"),
                field="product_sku",
                maximum_length=50,
                errors=errors,
            )
            .upper()
        )

        quantity_received = (
            cls._positive_quantity(
                row.get(
                    "quantity_received"
                ),
                field="quantity_received",
                errors=errors,
            )
        )

        notes = cls._optional_string(
            row.get(
                "notes",
                "",
            ),
            field="notes",
            maximum_length=1000,
            errors=errors,
        )

        # ==============================================
        # PURCHASE ORDER
        # ==============================================

        purchase_order = None

        if purchase_order_number:
            purchase_order = (
                PurchaseOrderRepository
                .get_by_po_number(
                    organization=organization,
                    po_number=(
                        purchase_order_number
                    ),
                )
            )

            if purchase_order is None:
                cls._add_error(
                    errors,
                    field=(
                        "purchase_order_number"
                    ),
                    code="PO_NOT_FOUND",
                    message=(
                        "Purchase order was not "
                        "found in the current "
                        "organization."
                    ),
                )

            elif purchase_order.status not in {
                "CONFIRMED",
                "PARTIALLY_RECEIVED",
            }:
                cls._add_error(
                    errors,
                    field=(
                        "purchase_order_number"
                    ),
                    code="INVALID_STATUS",
                    message=(
                        "Goods can only be received "
                        "against a confirmed or "
                        "partially received "
                        "purchase order."
                    ),
                )

        # ==============================================
        # WAREHOUSE
        # ==============================================

        warehouse = None

        if warehouse_code:
            warehouse = (
                WarehouseRepository
                .get_by_code(
                    organization=organization,
                    code=warehouse_code,
                )
            )

            if warehouse is None:
                cls._add_error(
                    errors,
                    field="warehouse_code",
                    code="WAREHOUSE_NOT_FOUND",
                    message=(
                        "Warehouse was not found "
                        "in the current "
                        "organization."
                    ),
                )

            elif not getattr(
                warehouse,
                "is_active",
                True,
            ):
                cls._add_error(
                    errors,
                    field="warehouse_code",
                    code="WAREHOUSE_INACTIVE",
                    message=(
                        "Warehouse is inactive."
                    ),
                )

        # ==============================================
        # PRODUCT
        # ==============================================

        product = None

        if product_sku:
            product = (
                ProductRepository
                .get_by_sku(
                    organization=organization,
                    sku=product_sku,
                )
            )

            if product is None:
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_NOT_FOUND",
                    message=(
                        "Product was not found "
                        "in the current "
                        "organization."
                    ),
                )

            elif not getattr(
                product,
                "is_active",
                True,
            ):
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_INACTIVE",
                    message=(
                        "Product is inactive."
                    ),
                )

        # ==============================================
        # PRODUCT MUST EXIST ON PURCHASE ORDER
        # ==============================================

        purchase_order_item = None

        if (
            purchase_order is not None
            and product is not None
        ):
            for item in (
                purchase_order.items or []
            ):
                item_product = getattr(
                    item,
                    "product",
                    None,
                )

                if (
                    item_product is not None
                    and str(item_product.id)
                    == str(product.id)
                ):
                    purchase_order_item = item
                    break

            if purchase_order_item is None:
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="PRODUCT_NOT_ON_PO",
                    message=(
                        "Product is not present "
                        "on the purchase order."
                    ),
                )

        # ==============================================
        # REMAINING QUANTITY
        # ==============================================

        if (
            purchase_order_item is not None
            and quantity_received is not None
        ):
            ordered_quantity = Decimal(
                str(
                    getattr(
                        purchase_order_item,
                        "quantity",
                        0,
                    )
                    or 0
                )
            )

            already_received = Decimal(
                str(
                    getattr(
                        purchase_order_item,
                        "received_quantity",
                        0,
                    )
                    or 0
                )
            )

            remaining_quantity = (
                ordered_quantity
                - already_received
            )

            if (
                quantity_received
                > remaining_quantity
            ):
                cls._add_error(
                    errors,
                    field="quantity_received",
                    code="EXCEEDS_REMAINING",
                    message=(
                        "Quantity received cannot "
                        "exceed the remaining "
                        "purchase order quantity."
                    ),
                )

        # ==============================================
        # DUPLICATE LINE IN MIGRATION FILE
        # ==============================================

        if (
            purchase_order_number
            and warehouse_code
            and product_sku
        ):
            line_key = (
                purchase_order_number,
                warehouse_code,
                product_sku,
            )

            if (
                line_key
                in seen_goods_receipt_lines
            ):
                cls._add_error(
                    errors,
                    field="product_sku",
                    code="DUPLICATE_IN_FILE",
                    message=(
                        "This product is duplicated "
                        "for the same purchase order "
                        "and warehouse in the "
                        "migration file."
                    ),
                )

            else:
                seen_goods_receipt_lines.add(
                    line_key
                )

        # ==============================================
        # NORMALIZED RESULT
        # ==============================================

        return {
            "valid": not errors,
            "errors": errors,
            "normalized": {
                "purchase_order_number":
                    purchase_order_number,
                "purchase_order_id": (
                    str(purchase_order.id)
                    if purchase_order is not None
                    else None
                ),
                "warehouse_code":
                    warehouse_code,
                "warehouse_id": (
                    str(warehouse.id)
                    if warehouse is not None
                    else None
                ),
                "product_sku":
                    product_sku,
                "product_id": (
                    str(product.id)
                    if product is not None
                    else None
                ),
                "quantity_received": (
                    str(quantity_received)
                    if quantity_received
                    is not None
                    else None
                ),
                "notes":
                    notes,
            },
        }
    # ==================================================
    # PUBLIC API
    # ==================================================

    @classmethod
    def validate_rows(
        cls,
        *,
        organization,
        migration_type,
        rows,
        skip_duplicates=False,
    ):
        migration_type = (
            str(migration_type or "")
            .strip()
            .upper()
        )

        if (
            migration_type
            not in cls.SUPPORTED_TYPES
        ):
            raise MigrationRowValidationError(
                "Row validation is not "
                "available for this "
                "migration type."
            )

        if not isinstance(
            rows,
            (
                list,
                tuple,
            ),
        ):
            raise MigrationRowValidationError(
                "Rows must be a list "
                "or tuple."
            )

        seen_financial = set()
        seen_category_names = set()
        seen_skus = set()
        seen_customer_codes = set()
        seen_supplier_codes = set()
        seen_warehouse_codes = set()
        seen_warehouse_names = set()
        seen_inventory_keys = set()
        seen_sales_order_lines = set()
        seen_purchase_order_lines = set()
        seen_invoice_numbers = set()
        seen_invoice_sales_orders = set()
        seen_goods_receipt_lines = set()

        results = []

        for index, row in enumerate(
            rows,
            start=2,
        ):
            if not isinstance(
                row,
                dict,
            ):
                results.append(
                    {
                        "row_number": index,
                        "valid": False,
                        "errors": [
                            {
                                "field": None,
                                "code":
                                    "INVALID_ROW",
                                "message":
                                    (
                                        "Row must be "
                                        "an object."
                                    ),
                            }
                        ],
                        "normalized": None,
                        "skipped": False,
                    }
                )

                continue

            if migration_type == "EMPLOYEES":
                from apps.migration.services.employee_import import validate_employee
                result=validate_employee(organization,row,seen_financial)
            elif migration_type in {"VENDOR_BILLS","CUSTOMER_PAYMENTS","SUPPLIER_PAYMENTS"}:
                from apps.migration.services.financial_import import validate_financial
                result=validate_financial(organization,migration_type,row,seen_financial)
            elif (
                migration_type
                ==
                "CATEGORIES"
            ):
                result = (
                    cls._validate_category_row(
                        organization=organization,
                        row=row,
                        seen_category_names=(
                            seen_category_names
                        ),
                    )
                )

            elif (
                migration_type
                ==
                "PRODUCTS"
            ):
                result = (
                    cls._validate_product_row(
                        organization=organization,
                        row=row,
                        seen_skus=seen_skus,
                    )
                )

            elif (
                migration_type
                ==
                "CUSTOMERS"
            ):
                result = (
                    cls._validate_customer_row(
                        organization=organization,
                        row=row,
                        seen_customer_codes=(
                            seen_customer_codes
                        ),
                    )
                )

            elif (
                migration_type
                ==
                "SUPPLIERS"
            ):
                result = (
                    cls._validate_supplier_row(
                        organization=organization,
                        row=row,
                        seen_supplier_codes=(
                            seen_supplier_codes
                        ),
                    )
                )

            elif (
                migration_type
                ==
                "WAREHOUSES"
            ):
                result = (
                    cls._validate_warehouse_row(
                        organization=organization,
                        row=row,
                        seen_warehouse_codes=(
                            seen_warehouse_codes
                        ),
                        seen_warehouse_names=(
                            seen_warehouse_names
                        ),
                    )
                )
            elif (
                migration_type
                ==
                "INVENTORY"
            ):
                result = (
                    cls._validate_inventory_row(
                        organization=organization,
                        row=row,
                        seen_inventory_keys=(
                            seen_inventory_keys
                        ),
                    )
                )
            elif (
                migration_type
                ==
                "SALES_ORDERS"
            ):
                result = (
                    cls._validate_sales_order_row(
                        organization=organization,
                        row=row,
                        seen_sales_order_lines=(
                            seen_sales_order_lines
                        ),
                    )
                )
            elif (
                migration_type
                ==
                "PURCHASE_ORDERS"
            ):
                result = (
                    cls._validate_purchase_order_row(
                        organization=organization,
                        row=row,
                        seen_purchase_order_lines=(
                            seen_purchase_order_lines
                        ),
                    )
                )
            elif (
                migration_type
                ==
                "SALES_INVOICES"
            ):
                result = (
                    cls._validate_sales_invoice_row(
                        organization=organization,
                        row=row,
                        seen_invoice_numbers=(
                            seen_invoice_numbers
                        ),
                        seen_invoice_sales_orders=(
                            seen_invoice_sales_orders
                        ),
                    )
                )
            elif (
                migration_type
                ==
                "GOODS_RECEIPTS"
            ):
                result = (
                    cls._validate_goods_receipt_row(
                        organization=organization,
                        row=row,
                        seen_goods_receipt_lines=(
                            seen_goods_receipt_lines
                        ),
                    )
                )
            else:
                raise (
                    MigrationRowValidationError(
                        "Row validation is not "
                        "available for this "
                        "migration type."
                    )
                )

            skipped = False

            if (
                skip_duplicates
                and not result.get(
                    "valid",
                    False,
                )
            ):
                errors = (
                    result.get("errors")
                    or []
                )

                error_codes = {
                    error.get("code")
                    for error in errors
                    if isinstance(
                        error,
                        dict,
                    )
                }

                if (
                    error_codes
                    == {"ALREADY_EXISTS"}
                ):
                    result = {
                        **result,
                        "valid": True,
                    }

                    skipped = True

            result["skipped"] = skipped

            results.append(
                {
                    "row_number": index,
                    **result,
                }
            )

        valid_rows = sum(
            1
            for result in results
            if result["valid"]
        )

        invalid_rows = (
            len(results)
            -
            valid_rows
        )

        return {
            "migration_type":
                migration_type,
            "total_rows":
                len(results),
            "valid_rows":
                valid_rows,
            "invalid_rows":
                invalid_rows,
            "can_import":
                (
                    bool(results)
                    and
                    invalid_rows == 0
                ),
            "rows":
                results,
        }