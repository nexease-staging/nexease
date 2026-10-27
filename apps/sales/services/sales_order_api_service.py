from datetime import (
    datetime,
)
from decimal import (
    Decimal,
    InvalidOperation,
)

from bson import (
    ObjectId,
)

from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.sales.repositories.customer_repository import (
    CustomerRepository,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.services.sales_order_service import (
    SalesOrderService,
)


class SalesOrderAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Sales order validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class SalesOrderAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class SalesOrderAPIService:

    CREATE_FIELDS = {
        "customer_id",
        "warehouse_id",
        "order_date",
        "expected_delivery_date",
        "items",
        "notes",
    }

    UPDATE_FIELDS = {
        "customer_id",
        "warehouse_id",
        "order_date",
        "expected_delivery_date",
        "items",
        "notes",
    }

    FULFILL_FIELDS = {
        "items",
        "notes",
    }

    PROTECTED_FIELDS = {
        "id",
        "_id",
        "organization",
        "organization_id",
        "so_number",
        "status",
        "subtotal",
        "tax_amount",
        "discount_amount",
        "total_amount",
        "created_by",
        "confirmed_at",
        "fulfilled_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise SalesOrderAPIValidationError(
            details={
                field: [
                    message,
                ],
            },
        )

    @staticmethod
    def _validate_payload_object(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise SalesOrderAPIValidationError(
                details={
                    "body": [
                        (
                            "JSON body must be "
                            "an object."
                        ),
                    ],
                },
            )

    @staticmethod
    def _validate_allowed_fields(
        payload,
        *,
        allowed_fields,
    ):
        errors = {}

        for field in payload:
            if field in (
                SalesOrderAPIService
                .PROTECTED_FIELDS
            ):
                errors[field] = [
                    (
                        "This field cannot be "
                        "changed directly."
                    ),
                ]

            elif field not in allowed_fields:
                errors[field] = [
                    "This field is not supported.",
                ]

        if errors:
            raise SalesOrderAPIValidationError(
                details=errors,
            )

    @staticmethod
    def _normalize_identifier(
        value,
        *,
        field,
    ):
        if (
            not isinstance(
                value,
                str,
            )
            or
            not ObjectId.is_valid(
                value.strip()
            )
        ):
            SalesOrderAPIService._raise_field_error(
                field,
                (
                    "This field must contain a "
                    "valid ObjectId."
                ),
            )

        return value.strip()

    @staticmethod
    def _normalize_sales_order_id(
        sales_order_id,
    ):
        return (
            SalesOrderAPIService
            ._normalize_identifier(
                sales_order_id,
                field="sales_order_id",
            )
        )

    @staticmethod
    def _normalize_datetime(
        value,
        *,
        field,
        required,
    ):
        if value in (
            None,
            "",
        ):
            if required:
                SalesOrderAPIService._raise_field_error(
                    field,
                    "This field is required.",
                )

            return None

        if not isinstance(
            value,
            str,
        ):
            SalesOrderAPIService._raise_field_error(
                field,
                (
                    "This field must be an "
                    "ISO-8601 datetime string."
                ),
            )

        normalized = value.strip()

        if normalized.endswith(
            "Z"
        ):
            normalized = (
                normalized[:-1]
                +
                "+00:00"
            )

        try:
            return datetime.fromisoformat(
                normalized
            )

        except ValueError as exc:
            raise SalesOrderAPIValidationError(
                details={
                    field: [
                        (
                            "Enter a valid ISO-8601 "
                            "date or datetime."
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def _normalize_decimal(
        value,
        *,
        field,
        greater_than_zero=False,
    ):
        if isinstance(
            value,
            bool,
        ):
            SalesOrderAPIService._raise_field_error(
                field,
                "Enter a valid number.",
            )

        try:
            decimal_value = Decimal(
                str(
                    value
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise SalesOrderAPIValidationError(
                details={
                    field: [
                        "Enter a valid number.",
                    ],
                },
            ) from exc

        if not decimal_value.is_finite():
            SalesOrderAPIService._raise_field_error(
                field,
                "Enter a finite number.",
            )

        if (
            decimal_value
            .as_tuple()
            .exponent
            <
            -2
        ):
            SalesOrderAPIService._raise_field_error(
                field,
                (
                    "This value cannot have more "
                    "than two decimal places."
                ),
            )

        if (
            greater_than_zero
            and
            decimal_value <= 0
        ):
            SalesOrderAPIService._raise_field_error(
                field,
                (
                    "This value must be greater "
                    "than zero."
                ),
            )

        if (
            not greater_than_zero
            and
            decimal_value < 0
        ):
            SalesOrderAPIService._raise_field_error(
                field,
                (
                    "This value cannot be "
                    "negative."
                ),
            )

        return decimal_value

    @staticmethod
    def _normalize_notes(
        value,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            SalesOrderAPIService._raise_field_error(
                "notes",
                (
                    "Notes must be a string "
                    "or null."
                ),
            )

        value = value.strip()

        if len(value) > 1000:
            SalesOrderAPIService._raise_field_error(
                "notes",
                (
                    "Notes cannot exceed "
                    "1000 characters."
                ),
            )

        return value

    @staticmethod
    def _resolve_customer(
        *,
        organization,
        customer_id,
    ):
        normalized_id = (
            SalesOrderAPIService
            ._normalize_identifier(
                customer_id,
                field="customer_id",
            )
        )

        customer = (
            CustomerRepository
            .get_by_id(
                organization=organization,
                customer_id=normalized_id,
            )
        )

        if not customer:
            SalesOrderAPIService._raise_field_error(
                "customer_id",
                (
                    "The selected customer "
                    "does not exist."
                ),
            )

        if not customer.is_active:
            SalesOrderAPIService._raise_field_error(
                "customer_id",
                (
                    "The selected customer "
                    "is inactive."
                ),
            )

        return customer

    @staticmethod
    def _resolve_warehouse(
        *,
        organization,
        warehouse_id,
    ):
        normalized_id = (
            SalesOrderAPIService
            ._normalize_identifier(
                warehouse_id,
                field="warehouse_id",
            )
        )

        warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=normalized_id,
            )
        )

        if not warehouse:
            SalesOrderAPIService._raise_field_error(
                "warehouse_id",
                (
                    "The selected warehouse "
                    "does not exist."
                ),
            )

        if not warehouse.is_active:
            SalesOrderAPIService._raise_field_error(
                "warehouse_id",
                (
                    "The selected warehouse "
                    "is inactive."
                ),
            )

        return warehouse

    @staticmethod
    def _resolve_product(
        *,
        organization,
        product_id,
        field,
    ):
        normalized_id = (
            SalesOrderAPIService
            ._normalize_identifier(
                product_id,
                field=field,
            )
        )

        product = (
            ProductRepository
            .get_by_id(
                organization=organization,
                product_id=normalized_id,
            )
        )

        if not product:
            SalesOrderAPIService._raise_field_error(
                field,
                (
                    "The selected product "
                    "does not exist."
                ),
            )

        if not product.is_active:
            SalesOrderAPIService._raise_field_error(
                field,
                (
                    "The selected product "
                    "is inactive."
                ),
            )

        return product

    @staticmethod
    def _normalize_items(
        *,
        organization,
        raw_items,
        fulfillment=False,
    ):
        if not isinstance(
            raw_items,
            list,
        ):
            SalesOrderAPIService._raise_field_error(
                "items",
                "Items must be a list.",
            )

        if not raw_items:
            SalesOrderAPIService._raise_field_error(
                "items",
                (
                    "At least one item is "
                    "required."
                ),
            )

        normalized_items = []
        product_ids = set()

        for index, raw_item in enumerate(
            raw_items
        ):
            item_field = (
                f"items.{index}"
            )

            if not isinstance(
                raw_item,
                dict,
            ):
                SalesOrderAPIService._raise_field_error(
                    item_field,
                    (
                        "Each item must be "
                        "an object."
                    ),
                )

            allowed_item_fields = (
                {
                    "product_id",
                    "quantity",
                }
                if fulfillment
                else
                {
                    "product_id",
                    "quantity",
                    "unit_price",
                    "tax_rate",
                    "discount",
                }
            )

            unknown_fields = (
                set(
                    raw_item.keys()
                )
                -
                allowed_item_fields
            )

            if unknown_fields:
                SalesOrderAPIService._raise_field_error(
                    item_field,
                    (
                        "Unsupported item fields: "
                        +
                        ", ".join(
                            sorted(
                                unknown_fields
                            )
                        )
                        +
                        "."
                    ),
                )

            required_fields = {
                "product_id",
                "quantity",
            }

            if not fulfillment:
                required_fields.add(
                    "unit_price"
                )

            missing_fields = (
                required_fields
                -
                set(
                    raw_item.keys()
                )
            )

            if missing_fields:
                SalesOrderAPIService._raise_field_error(
                    item_field,
                    (
                        "Missing required fields: "
                        +
                        ", ".join(
                            sorted(
                                missing_fields
                            )
                        )
                        +
                        "."
                    ),
                )

            product = (
                SalesOrderAPIService
                ._resolve_product(
                    organization=organization,
                    product_id=raw_item.get(
                        "product_id"
                    ),
                    field=(
                        f"{item_field}.product_id"
                    ),
                )
            )

            product_id = str(
                product.id
            )

            if product_id in product_ids:
                SalesOrderAPIService._raise_field_error(
                    f"{item_field}.product_id",
                    (
                        "The same product cannot "
                        "appear more than once."
                    ),
                )

            product_ids.add(
                product_id
            )

            normalized_item = {
                "product":
                    product,
                "quantity": (
                    SalesOrderAPIService
                    ._normalize_decimal(
                        raw_item.get(
                            "quantity"
                        ),
                        field=(
                            f"{item_field}.quantity"
                        ),
                        greater_than_zero=True,
                    )
                ),
            }

            if not fulfillment:
                normalized_item.update({
                    "unit_price": (
                        SalesOrderAPIService
                        ._normalize_decimal(
                            raw_item.get(
                                "unit_price"
                            ),
                            field=(
                                f"{item_field}.unit_price"
                            ),
                        )
                    ),
                    "tax_rate": (
                        SalesOrderAPIService
                        ._normalize_decimal(
                            raw_item.get(
                                "tax_rate",
                                0,
                            ),
                            field=(
                                f"{item_field}.tax_rate"
                            ),
                        )
                    ),
                    "discount": (
                        SalesOrderAPIService
                        ._normalize_decimal(
                            raw_item.get(
                                "discount",
                                0,
                            ),
                            field=(
                                f"{item_field}.discount"
                            ),
                        )
                    ),
                })

            normalized_items.append(
                normalized_item
            )

        return normalized_items

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        SalesOrderAPIService._validate_payload_object(
            payload
        )

        SalesOrderAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                SalesOrderAPIService
                .CREATE_FIELDS
            ),
        )

        required_fields = {
            "customer_id",
            "warehouse_id",
            "order_date",
            "items",
        }

        missing_fields = (
            required_fields
            -
            set(
                payload.keys()
            )
        )

        if missing_fields:
            raise SalesOrderAPIValidationError(
                details={
                    field: [
                        "This field is required.",
                    ]
                    for field
                    in sorted(
                        missing_fields
                    )
                },
            )

        customer = (
            SalesOrderAPIService
            ._resolve_customer(
                organization=organization,
                customer_id=payload.get(
                    "customer_id"
                ),
            )
        )

        warehouse = (
            SalesOrderAPIService
            ._resolve_warehouse(
                organization=organization,
                warehouse_id=payload.get(
                    "warehouse_id"
                ),
            )
        )

        order_date = (
            SalesOrderAPIService
            ._normalize_datetime(
                payload.get(
                    "order_date"
                ),
                field="order_date",
                required=True,
            )
        )

        expected_delivery_date = (
            SalesOrderAPIService
            ._normalize_datetime(
                payload.get(
                    "expected_delivery_date"
                ),
                field=(
                    "expected_delivery_date"
                ),
                required=False,
            )
        )

        if (
            expected_delivery_date
            and
            expected_delivery_date
            <
            order_date
        ):
            SalesOrderAPIService._raise_field_error(
                "expected_delivery_date",
                (
                    "Expected delivery date cannot "
                    "be earlier than order date."
                ),
            )

        return {
            "customer":
                customer,
            "warehouse":
                warehouse,
            "order_date":
                order_date,
            "expected_delivery_date": (
                expected_delivery_date
            ),
            "raw_items": (
                SalesOrderAPIService
                ._normalize_items(
                    organization=organization,
                    raw_items=payload.get(
                        "items"
                    ),
                )
            ),
            "notes": (
                SalesOrderAPIService
                ._normalize_notes(
                    payload.get(
                        "notes",
                        "",
                    )
                )
            ),
        }

    @staticmethod
    def validate_update_payload(
        *,
        organization,
        sales_order,
        payload,
    ):
        SalesOrderAPIService._validate_payload_object(
            payload
        )

        if not payload:
            SalesOrderAPIService._raise_field_error(
                "body",
                (
                    "At least one editable field "
                    "is required."
                ),
            )

        SalesOrderAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                SalesOrderAPIService
                .UPDATE_FIELDS
            ),
        )

        values = {}

        if "customer_id" in payload:
            values["customer"] = (
                SalesOrderAPIService
                ._resolve_customer(
                    organization=organization,
                    customer_id=payload[
                        "customer_id"
                    ],
                )
            )

        if "warehouse_id" in payload:
            values["warehouse"] = (
                SalesOrderAPIService
                ._resolve_warehouse(
                    organization=organization,
                    warehouse_id=payload[
                        "warehouse_id"
                    ],
                )
            )

        if "order_date" in payload:
            values["order_date"] = (
                SalesOrderAPIService
                ._normalize_datetime(
                    payload[
                        "order_date"
                    ],
                    field="order_date",
                    required=True,
                )
            )

        if (
            "expected_delivery_date"
            in payload
        ):
            expected_delivery_date = (
                SalesOrderAPIService
                ._normalize_datetime(
                    payload[
                        "expected_delivery_date"
                    ],
                    field=(
                        "expected_delivery_date"
                    ),
                    required=False,
                )
            )

            if expected_delivery_date is None:
                SalesOrderAPIService._raise_field_error(
                    "expected_delivery_date",
                    (
                        "Use a valid date when "
                        "updating this field."
                    ),
                )

            values[
                "expected_delivery_date"
            ] = expected_delivery_date

        if "items" in payload:
            values["raw_items"] = (
                SalesOrderAPIService
                ._normalize_items(
                    organization=organization,
                    raw_items=payload[
                        "items"
                    ],
                )
            )

        if "notes" in payload:
            values["notes"] = (
                SalesOrderAPIService
                ._normalize_notes(
                    payload[
                        "notes"
                    ]
                )
            )

        effective_order_date = (
            values.get(
                "order_date",
                sales_order.order_date,
            )
        )

        effective_delivery_date = (
            values.get(
                "expected_delivery_date",
                (
                    sales_order
                    .expected_delivery_date
                ),
            )
        )

        if (
            effective_delivery_date
            and
            effective_delivery_date
            <
            effective_order_date
        ):
            SalesOrderAPIService._raise_field_error(
                "expected_delivery_date",
                (
                    "Expected delivery date cannot "
                    "be earlier than order date."
                ),
            )

        return values

    @staticmethod
    def validate_fulfillment_payload(
        *,
        organization,
        payload,
    ):
        SalesOrderAPIService._validate_payload_object(
            payload
        )

        SalesOrderAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                SalesOrderAPIService
                .FULFILL_FIELDS
            ),
        )

        if "items" not in payload:
            SalesOrderAPIService._raise_field_error(
                "items",
                "This field is required.",
            )

        return {
            "raw_items": (
                SalesOrderAPIService
                ._normalize_items(
                    organization=organization,
                    raw_items=payload[
                        "items"
                    ],
                    fulfillment=True,
                )
            ),
            "notes": (
                SalesOrderAPIService
                ._normalize_notes(
                    payload.get(
                        "notes",
                        "",
                    )
                )
            ),
        }

    @staticmethod
    def get_sales_order(
        *,
        organization,
        sales_order_id,
    ):
        normalized_id = (
            SalesOrderAPIService
            ._normalize_sales_order_id(
                sales_order_id
            )
        )

        sales_order = (
            SalesOrderRepository
            .get_by_id(
                organization=organization,
                sales_order_id=normalized_id,
            )
        )

        if not sales_order:
            raise LookupError(
                "Sales order not found."
            )

        return sales_order

    @staticmethod
    def create_sales_order(
        *,
        user,
        organization,
        payload,
    ):
        if not organization:
            raise PermissionError(
                (
                    "Organization context "
                    "is unavailable."
                )
            )

        values = (
            SalesOrderAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                SalesOrderService
                .create_sales_order(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesOrderAPIValidationError(
                message=str(
                    exc
                ),
                details={
                    "sales_order": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def update_sales_order(
        *,
        user,
        organization,
        sales_order_id,
        payload,
    ):
        sales_order = (
            SalesOrderAPIService
            .get_sales_order(
                organization=organization,
                sales_order_id=sales_order_id,
            )
        )

        if sales_order.status != "DRAFT":
            raise SalesOrderAPIStateError(
                message=(
                    "Only draft sales orders "
                    "can be edited."
                ),
                details={
                    "status": [
                        (
                            "The current sales-order "
                            "status does not allow "
                            "editing."
                        ),
                    ],
                },
            )

        values = (
            SalesOrderAPIService
            .validate_update_payload(
                organization=organization,
                sales_order=sales_order,
                payload=payload,
            )
        )

        try:
            return (
                SalesOrderService
                .update_sales_order(
                    user=user,
                    organization=organization,
                    sales_order_id=(
                        sales_order_id
                    ),
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesOrderAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "sales_order": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def confirm_sales_order(
        *,
        user,
        organization,
        sales_order_id,
    ):
        SalesOrderAPIService.get_sales_order(
            organization=organization,
            sales_order_id=sales_order_id,
        )

        try:
            return (
                SalesOrderService
                .confirm_sales_order(
                    user=user,
                    organization=organization,
                    sales_order_id=(
                        sales_order_id
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesOrderAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "sales_order": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def cancel_sales_order(
        *,
        user,
        organization,
        sales_order_id,
    ):
        SalesOrderAPIService.get_sales_order(
            organization=organization,
            sales_order_id=sales_order_id,
        )

        try:
            return (
                SalesOrderService
                .cancel_sales_order(
                    user=user,
                    organization=organization,
                    sales_order_id=(
                        sales_order_id
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesOrderAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "sales_order": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def fulfill_sales_order(
        *,
        user,
        organization,
        sales_order_id,
        payload,
    ):
        SalesOrderAPIService.get_sales_order(
            organization=organization,
            sales_order_id=sales_order_id,
        )

        values = (
            SalesOrderAPIService
            .validate_fulfillment_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                SalesOrderService
                .fulfill_sales_order(
                    user=user,
                    organization=organization,
                    sales_order_id=(
                        sales_order_id
                    ),
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise SalesOrderAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "sales_order": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc
