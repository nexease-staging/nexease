from datetime import (
    date,
)
from decimal import (
    Decimal,
    InvalidOperation,
)

from bson import (
    ObjectId,
)

from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from apps.purchasing.repositories.supplier_repository import (
    SupplierRepository,
)
from apps.purchasing.services.purchase_order_service import (
    PurchaseOrderService,
)


class PurchaseOrderAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class PurchaseOrderAPIStateError(
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


class PurchaseOrderAPIService:

    CREATE_FIELDS = {
        "supplier_id",
        "order_date",
        "expected_delivery_date",
        "items",
        "notes",
    }

    UPDATE_FIELDS = {
        "supplier_id",
        "order_date",
        "expected_delivery_date",
        "items",
        "notes",
    }

    ITEM_FIELDS = {
        "product_id",
        "quantity",
        "unit_price",
        "tax_rate",
        "discount",
    }

    REQUIRED_CREATE_FIELDS = {
        "supplier_id",
        "order_date",
        "items",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise PurchaseOrderAPIValidationError(
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
            raise PurchaseOrderAPIValidationError(
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
        unexpected = (
            set(
                payload.keys()
            )
            -
            allowed_fields
        )

        if unexpected:
            raise PurchaseOrderAPIValidationError(
                details={
                    field: [
                        (
                            "This field is not "
                            "allowed."
                        ),
                    ]
                    for field
                    in sorted(
                        unexpected
                    )
                },
            )

    @staticmethod
    def _parse_identifier(
        value,
        *,
        field,
    ):
        if not isinstance(
            value,
            str,
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    (
                        "Identifier must "
                        "be a string."
                    ),
                )
            )

        value = value.strip()

        if not ObjectId.is_valid(
            value
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    (
                        "Enter a valid "
                        "identifier."
                    ),
                )
            )

        return ObjectId(
            value
        )

    @staticmethod
    def _normalize_date(
        value,
        *,
        field,
        required=False,
    ):
        if value in {
            None,
            "",
        }:
            if required:
                (
                    PurchaseOrderAPIService
                    ._raise_field_error(
                        field,
                        "This field is required.",
                    )
                )

            return None

        if not isinstance(
            value,
            str,
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    (
                        "Date must be an "
                        "ISO date string."
                    ),
                )
            )

        try:
            return date.fromisoformat(
                value.strip()
            )

        except ValueError:
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    (
                        "Enter a valid date "
                        "in YYYY-MM-DD format."
                    ),
                )
            )

    @staticmethod
    def _normalize_decimal(
        value,
        *,
        field,
        positive=False,
    ):
        if isinstance(
            value,
            bool,
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    "Enter a valid number.",
                )
            )

        try:
            normalized = Decimal(
                str(
                    value
                ).strip()
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    "Enter a valid number.",
                )
            )

        if not normalized.is_finite():
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    "Enter a finite number.",
                )
            )

        if (
            positive
            and
            normalized <= 0
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    (
                        "Value must be greater "
                        "than zero."
                    ),
                )
            )

        if (
            not positive
            and
            normalized < 0
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    (
                        "Value cannot be "
                        "negative."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_optional_text(
        value,
        *,
        field,
        maximum_length,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    "Value must be a string.",
                )
            )

        value = value.strip()

        if len(value) > maximum_length:
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    field,
                    (
                        "Value cannot exceed "
                        f"{maximum_length} "
                        "characters."
                    ),
                )
            )

        return value

    @staticmethod
    def _resolve_supplier(
        *,
        organization,
        supplier_id,
    ):
        parsed_supplier_id = (
            PurchaseOrderAPIService
            ._parse_identifier(
                supplier_id,
                field="supplier_id",
            )
        )

        supplier = (
            SupplierRepository
            .get_by_id(
                organization=organization,
                supplier_id=(
                    parsed_supplier_id
                ),
            )
        )

        if (
            not supplier
            or
            not supplier.is_active
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    "supplier_id",
                    (
                        "Select a valid active "
                        "supplier."
                    ),
                )
            )

        return supplier

    @staticmethod
    def _normalize_items(
        *,
        organization,
        items,
    ):
        if not isinstance(
            items,
            list,
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    "items",
                    (
                        "Items must be "
                        "an array."
                    ),
                )
            )

        if not items:
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    "items",
                    (
                        "At least one item "
                        "is required."
                    ),
                )
            )

        normalized_items = []
        product_ids = set()

        for (
            index,
            item,
        ) in enumerate(
            items
        ):
            item_field = (
                f"items.{index}"
            )

            if not isinstance(
                item,
                dict,
            ):
                (
                    PurchaseOrderAPIService
                    ._raise_field_error(
                        item_field,
                        (
                            "Item must be "
                            "an object."
                        ),
                    )
                )

            unexpected = (
                set(
                    item.keys()
                )
                -
                PurchaseOrderAPIService
                .ITEM_FIELDS
            )

            if unexpected:
                (
                    PurchaseOrderAPIService
                    ._raise_field_error(
                        item_field,
                        (
                            "Item contains "
                            "unsupported fields."
                        ),
                    )
                )

            required_fields = {
                "product_id",
                "quantity",
                "unit_price",
            }

            missing_fields = (
                required_fields
                -
                set(
                    item.keys()
                )
            )

            if missing_fields:
                (
                    PurchaseOrderAPIService
                    ._raise_field_error(
                        item_field,
                        (
                            "Product, quantity "
                            "and unit price "
                            "are required."
                        ),
                    )
                )

            parsed_product_id = (
                PurchaseOrderAPIService
                ._parse_identifier(
                    item.get(
                        "product_id"
                    ),
                    field=(
                        f"{item_field}"
                        ".product_id"
                    ),
                )
            )

            product_key = str(
                parsed_product_id
            )

            if product_key in product_ids:
                (
                    PurchaseOrderAPIService
                    ._raise_field_error(
                        "items",
                        (
                            "Duplicate products "
                            "are not allowed."
                        ),
                    )
                )

            product = (
                ProductRepository
                .get_by_id(
                    organization=organization,
                    product_id=(
                        parsed_product_id
                    ),
                )
            )

            if (
                not product
                or
                not product.is_active
            ):
                (
                    PurchaseOrderAPIService
                    ._raise_field_error(
                        (
                            f"{item_field}"
                            ".product_id"
                        ),
                        (
                            "Select a valid active "
                            "product."
                        ),
                    )
                )

            product_ids.add(
                product_key
            )

            normalized_items.append({
                "product":
                    product,
                "quantity": (
                    PurchaseOrderAPIService
                    ._normalize_decimal(
                        item.get(
                            "quantity"
                        ),
                        field=(
                            f"{item_field}"
                            ".quantity"
                        ),
                        positive=True,
                    )
                ),
                "unit_price": (
                    PurchaseOrderAPIService
                    ._normalize_decimal(
                        item.get(
                            "unit_price"
                        ),
                        field=(
                            f"{item_field}"
                            ".unit_price"
                        ),
                    )
                ),
                "tax_rate": (
                    PurchaseOrderAPIService
                    ._normalize_decimal(
                        item.get(
                            "tax_rate",
                            0,
                        ),
                        field=(
                            f"{item_field}"
                            ".tax_rate"
                        ),
                    )
                ),
                "discount": (
                    PurchaseOrderAPIService
                    ._normalize_decimal(
                        item.get(
                            "discount",
                            0,
                        ),
                        field=(
                            f"{item_field}"
                            ".discount"
                        ),
                    )
                ),
            })

        return normalized_items

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        (
            PurchaseOrderAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            PurchaseOrderAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    PurchaseOrderAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        missing_fields = (
            PurchaseOrderAPIService
            .REQUIRED_CREATE_FIELDS
            -
            set(
                payload.keys()
            )
        )

        if missing_fields:
            raise PurchaseOrderAPIValidationError(
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

        supplier = (
            PurchaseOrderAPIService
            ._resolve_supplier(
                organization=organization,
                supplier_id=payload.get(
                    "supplier_id"
                ),
            )
        )

        order_date = (
            PurchaseOrderAPIService
            ._normalize_date(
                payload.get(
                    "order_date"
                ),
                field="order_date",
                required=True,
            )
        )

        expected_delivery_date = (
            PurchaseOrderAPIService
            ._normalize_date(
                payload.get(
                    "expected_delivery_date"
                ),
                field=(
                    "expected_delivery_date"
                ),
            )
        )

        if (
            expected_delivery_date
            and
            expected_delivery_date
            <
            order_date
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    "expected_delivery_date",
                    (
                        "Expected delivery date "
                        "cannot be before the "
                        "order date."
                    ),
                )
            )

        return {
            "supplier":
                supplier,
            "order_date":
                order_date,
            "expected_delivery_date": (
                expected_delivery_date
            ),
            "raw_items": (
                PurchaseOrderAPIService
                ._normalize_items(
                    organization=organization,
                    items=payload.get(
                        "items"
                    ),
                )
            ),
            "notes": (
                PurchaseOrderAPIService
                ._normalize_optional_text(
                    payload.get(
                        "notes",
                        "",
                    ),
                    field="notes",
                    maximum_length=1000,
                )
            ),
        }

    @staticmethod
    def validate_update_payload(
        *,
        organization,
        payload,
        purchase_order,
    ):
        (
            PurchaseOrderAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            PurchaseOrderAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    PurchaseOrderAPIService
                    .UPDATE_FIELDS
                ),
            )
        )

        if not payload:
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    "body",
                    (
                        "Provide at least one "
                        "field to update."
                    ),
                )
            )

        values = {}

        if "supplier_id" in payload:
            values["supplier"] = (
                PurchaseOrderAPIService
                ._resolve_supplier(
                    organization=organization,
                    supplier_id=payload.get(
                        "supplier_id"
                    ),
                )
            )

        if "order_date" in payload:
            values["order_date"] = (
                PurchaseOrderAPIService
                ._normalize_date(
                    payload.get(
                        "order_date"
                    ),
                    field="order_date",
                    required=True,
                )
            )

        if (
            "expected_delivery_date"
            in payload
        ):
            expected_delivery_date = (
                PurchaseOrderAPIService
                ._normalize_date(
                    payload.get(
                        "expected_delivery_date"
                    ),
                    field=(
                        "expected_delivery_date"
                    ),
                )
            )

            if expected_delivery_date is None:
                (
                    PurchaseOrderAPIService
                    ._raise_field_error(
                        (
                            "expected_delivery_date"
                        ),
                        (
                            "Expected delivery date "
                            "cannot be empty when "
                            "provided."
                        ),
                    )
                )

            values[
                "expected_delivery_date"
            ] = expected_delivery_date

        effective_order_date = (
            values.get(
                "order_date"
            )
            or
            purchase_order.order_date
        )

        effective_delivery_date = (
            values.get(
                "expected_delivery_date"
            )
            or
            (
                purchase_order
                .expected_delivery_date
            )
        )

        if (
            effective_delivery_date
            and
            effective_delivery_date
            <
            effective_order_date
        ):
            (
                PurchaseOrderAPIService
                ._raise_field_error(
                    "expected_delivery_date",
                    (
                        "Expected delivery date "
                        "cannot be before the "
                        "order date."
                    ),
                )
            )

        if "items" in payload:
            values["raw_items"] = (
                PurchaseOrderAPIService
                ._normalize_items(
                    organization=organization,
                    items=payload.get(
                        "items"
                    ),
                )
            )

        if "notes" in payload:
            values["notes"] = (
                PurchaseOrderAPIService
                ._normalize_optional_text(
                    payload.get(
                        "notes"
                    ),
                    field="notes",
                    maximum_length=1000,
                )
            )

        return values

    @staticmethod
    def get_purchase_order(
        *,
        organization,
        purchase_order_id,
    ):
        parsed_purchase_order_id = (
            PurchaseOrderAPIService
            ._parse_identifier(
                purchase_order_id,
                field="purchase_order_id",
            )
        )

        purchase_order = (
            PurchaseOrderRepository
            .get_by_id(
                organization=organization,
                purchase_order_id=(
                    parsed_purchase_order_id
                ),
            )
        )

        if not purchase_order:
            raise LookupError(
                "Purchase order not found."
            )

        return purchase_order

    @staticmethod
    def create_purchase_order(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            PurchaseOrderAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                PurchaseOrderService
                .create_purchase_order(
                    user=user,
                    organization=organization,
                    supplier=values[
                        "supplier"
                    ],
                    order_date=values[
                        "order_date"
                    ],
                    expected_delivery_date=(
                        values[
                            "expected_delivery_date"
                        ]
                    ),
                    raw_items=values[
                        "raw_items"
                    ],
                    notes=values[
                        "notes"
                    ],
                )
            )

        except ValueError as exc:
            raise (
                PurchaseOrderAPIValidationError(
                    message=str(
                        exc
                    ),
                    details={
                        "body": [
                            str(
                                exc
                            ),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def update_purchase_order(
        *,
        user,
        organization,
        purchase_order_id,
        payload,
    ):
        purchase_order = (
            PurchaseOrderAPIService
            .get_purchase_order(
                organization=organization,
                purchase_order_id=(
                    purchase_order_id
                ),
            )
        )

        if (
            purchase_order.status
            !=
            "DRAFT"
        ):
            raise PurchaseOrderAPIStateError(
                message=(
                    "Only draft purchase orders "
                    "can be updated."
                ),
                details={
                    "status": [
                        purchase_order.status,
                    ],
                },
            )

        values = (
            PurchaseOrderAPIService
            .validate_update_payload(
                organization=organization,
                payload=payload,
                purchase_order=(
                    purchase_order
                ),
            )
        )

        try:
            return (
                PurchaseOrderService
                .update_purchase_order(
                    user=user,
                    organization=organization,
                    purchase_order_id=(
                        purchase_order.id
                    ),
                    supplier=values.get(
                        "supplier"
                    ),
                    order_date=values.get(
                        "order_date"
                    ),
                    expected_delivery_date=(
                        values.get(
                            "expected_delivery_date"
                        )
                    ),
                    raw_items=values.get(
                        "raw_items"
                    ),
                    notes=values.get(
                        "notes"
                    ),
                )
            )

        except ValueError as exc:
            raise (
                PurchaseOrderAPIValidationError(
                    message=str(
                        exc
                    ),
                    details={
                        "body": [
                            str(
                                exc
                            ),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def confirm_purchase_order(
        *,
        user,
        organization,
        purchase_order_id,
    ):
        purchase_order = (
            PurchaseOrderAPIService
            .get_purchase_order(
                organization=organization,
                purchase_order_id=(
                    purchase_order_id
                ),
            )
        )

        if (
            purchase_order.status
            !=
            "DRAFT"
        ):
            raise PurchaseOrderAPIStateError(
                message=(
                    "Only draft purchase orders "
                    "can be confirmed."
                ),
                details={
                    "status": [
                        purchase_order.status,
                    ],
                },
            )

        return (
            PurchaseOrderService
            .confirm_purchase_order(
                user=user,
                organization=organization,
                purchase_order_id=(
                    purchase_order.id
                ),
            )
        )

    @staticmethod
    def cancel_purchase_order(
        *,
        user,
        organization,
        purchase_order_id,
    ):
        purchase_order = (
            PurchaseOrderAPIService
            .get_purchase_order(
                organization=organization,
                purchase_order_id=(
                    purchase_order_id
                ),
            )
        )

        if (
            purchase_order.status
            ==
            "CANCELLED"
        ):
            raise PurchaseOrderAPIStateError(
                message=(
                    "Purchase order is already "
                    "cancelled."
                ),
                details={
                    "status": [
                        purchase_order.status,
                    ],
                },
            )

        if purchase_order.status in {
            "PARTIALLY_RECEIVED",
            "RECEIVED",
        }:
            raise PurchaseOrderAPIStateError(
                message=(
                    "Received purchase orders "
                    "cannot be cancelled."
                ),
                details={
                    "status": [
                        purchase_order.status,
                    ],
                },
            )

        return (
            PurchaseOrderService
            .cancel_purchase_order(
                user=user,
                organization=organization,
                purchase_order_id=(
                    purchase_order.id
                ),
            )
        )