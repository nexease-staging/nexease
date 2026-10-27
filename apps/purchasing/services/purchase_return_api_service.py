from datetime import datetime
from decimal import (
    Decimal,
    InvalidOperation,
)

from bson import ObjectId

from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from apps.purchasing.repositories.purchase_return_repository import (
    PurchaseReturnRepository,
)
from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
)
from apps.purchasing.services.purchase_return_service import (
    PurchaseReturnService,
)


class PurchaseReturnAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Purchase return validation "
            "failed."
        ),
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class PurchaseReturnAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class PurchaseReturnAPIService:

    CREATE_FIELDS = {
        "purchase_order_id",
        "vendor_bill_id",
        "warehouse_id",
        "return_date",
        "items",
        "reason",
        "notes",
    }

    ITEM_FIELDS = {
        "product_id",
        "quantity",
        "reason",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            PurchaseReturnAPIValidationError(
                details={
                    field: [
                        message,
                    ],
                },
            )
        )

    @staticmethod
    def _validate_payload_object(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise (
                PurchaseReturnAPIValidationError(
                    details={
                        "body": [
                            (
                                "JSON body must be "
                                "an object."
                            ),
                        ],
                    },
                )
            )

    @staticmethod
    def _validate_allowed_fields(
        payload,
        *,
        allowed_fields,
    ):
        unknown_fields = (
            set(
                payload.keys()
            )
            -
            allowed_fields
        )

        if unknown_fields:
            raise (
                PurchaseReturnAPIValidationError(
                    details={
                        field: [
                            (
                                "This field is not "
                                "supported."
                            ),
                        ]
                        for field
                        in sorted(
                            unknown_fields
                        )
                    },
                )
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
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid ObjectId."
                    ),
                )
            )

        return value.strip()

    @staticmethod
    def _normalize_datetime(
        value,
        *,
        field,
    ):
        if value in (
            None,
            "",
        ):
            return None

        if not isinstance(
            value,
            str,
        ):
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be an "
                        "ISO-8601 date or datetime."
                    ),
                )
            )

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1]
                +
                "+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )

        except ValueError:
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    field,
                    (
                        "Enter a valid ISO-8601 "
                        "date or datetime."
                    ),
                )
            )

        if parsed.tzinfo is not None:
            parsed = parsed.replace(
                tzinfo=None,
            )

        return parsed

    @staticmethod
    def _normalize_text(
        value,
        *,
        field,
        maximum_length,
    ):
        if value in (
            None,
            "",
        ):
            return ""

        if not isinstance(
            value,
            str,
        ):
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    field,
                    "This field must be a string.",
                )
            )

        normalized = value.strip()

        if (
            len(normalized)
            >
            maximum_length
        ):
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must not exceed "
                        f"{maximum_length} characters."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_quantity(
        value,
        *,
        field,
    ):
        try:
            quantity = Decimal(
                str(value)
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    field,
                    (
                        "Enter a valid return "
                        "quantity."
                    ),
                )
            )

        if quantity <= 0:
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    field,
                    (
                        "Return quantity must be "
                        "greater than zero."
                    ),
                )
            )

        return quantity

    @staticmethod
    def _normalize_items(
        *,
        organization,
        value,
    ):
        if not isinstance(
            value,
            list,
        ):
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    "items",
                    "This field must be a list.",
                )
            )

        if not value:
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    "items",
                    (
                        "At least one return item "
                        "is required."
                    ),
                )
            )

        normalized_items = []
        seen_product_ids = set()

        for index, item in enumerate(
            value
        ):
            item_field = (
                f"items.{index}"
            )

            if not isinstance(
                item,
                dict,
            ):
                (
                    PurchaseReturnAPIService
                    ._raise_field_error(
                        item_field,
                        (
                            "Each item must be "
                            "an object."
                        ),
                    )
                )

            unknown_fields = (
                set(
                    item.keys()
                )
                -
                PurchaseReturnAPIService
                .ITEM_FIELDS
            )

            if unknown_fields:
                raise (
                    PurchaseReturnAPIValidationError(
                        details={
                            (
                                f"{item_field}."
                                f"{field}"
                            ): [
                                (
                                    "This field is "
                                    "not supported."
                                ),
                            ]
                            for field
                            in sorted(
                                unknown_fields
                            )
                        },
                    )
                )

            product_id = (
                PurchaseReturnAPIService
                ._normalize_identifier(
                    item.get(
                        "product_id"
                    ),
                    field=(
                        f"{item_field}."
                        "product_id"
                    ),
                )
            )

            if product_id in seen_product_ids:
                (
                    PurchaseReturnAPIService
                    ._raise_field_error(
                        (
                            f"{item_field}."
                            "product_id"
                        ),
                        (
                            "Duplicate products are "
                            "not allowed."
                        ),
                    )
                )

            product = (
                ProductRepository
                .get_by_id(
                    organization=organization,
                    product_id=product_id,
                )
            )

            if not product:
                (
                    PurchaseReturnAPIService
                    ._raise_field_error(
                        (
                            f"{item_field}."
                            "product_id"
                        ),
                        (
                            "Product was not found "
                            "in this organization."
                        ),
                    )
                )

            quantity = (
                PurchaseReturnAPIService
                ._normalize_quantity(
                    item.get(
                        "quantity"
                    ),
                    field=(
                        f"{item_field}."
                        "quantity"
                    ),
                )
            )

            reason = (
                PurchaseReturnAPIService
                ._normalize_text(
                    item.get(
                        "reason"
                    ),
                    field=(
                        f"{item_field}."
                        "reason"
                    ),
                    maximum_length=500,
                )
            )

            seen_product_ids.add(
                product_id
            )

            normalized_items.append({
                "product":
                    product,
                "quantity":
                    quantity,
                "reason":
                    reason,
            })

        return normalized_items

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        (
            PurchaseReturnAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            PurchaseReturnAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    PurchaseReturnAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        purchase_order_id = (
            PurchaseReturnAPIService
            ._normalize_identifier(
                payload.get(
                    "purchase_order_id"
                ),
                field="purchase_order_id",
            )
        )

        vendor_bill_id = (
            PurchaseReturnAPIService
            ._normalize_identifier(
                payload.get(
                    "vendor_bill_id"
                ),
                field="vendor_bill_id",
            )
        )

        warehouse_id = (
            PurchaseReturnAPIService
            ._normalize_identifier(
                payload.get(
                    "warehouse_id"
                ),
                field="warehouse_id",
            )
        )

        purchase_order = (
            PurchaseOrderRepository
            .get_by_id(
                organization=organization,
                purchase_order_id=(
                    purchase_order_id
                ),
            )
        )

        if not purchase_order:
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    "purchase_order_id",
                    (
                        "Purchase order was not "
                        "found in this organization."
                    ),
                )
            )

        vendor_bill = (
            VendorBillRepository
            .get_by_id(
                organization=organization,
                bill_id=vendor_bill_id,
            )
        )

        if not vendor_bill:
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    "vendor_bill_id",
                    (
                        "Vendor bill was not found "
                        "in this organization."
                    ),
                )
            )

        warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if not warehouse:
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    "warehouse_id",
                    (
                        "Warehouse was not found "
                        "in this organization."
                    ),
                )
            )

        if (
            not vendor_bill.purchase_order
            or vendor_bill.purchase_order.id
            != purchase_order.id
        ):
            (
                PurchaseReturnAPIService
                ._raise_field_error(
                    "vendor_bill_id",
                    (
                        "Vendor bill does not "
                        "belong to the selected "
                        "purchase order."
                    ),
                )
            )

        return {
            "purchase_order":
                purchase_order,
            "vendor_bill":
                vendor_bill,
            "warehouse":
                warehouse,
            "return_date": (
                PurchaseReturnAPIService
                ._normalize_datetime(
                    payload.get(
                        "return_date"
                    ),
                    field="return_date",
                )
            ),
            "items": (
                PurchaseReturnAPIService
                ._normalize_items(
                    organization=organization,
                    value=payload.get(
                        "items"
                    ),
                )
            ),
            "reason": (
                PurchaseReturnAPIService
                ._normalize_text(
                    payload.get(
                        "reason"
                    ),
                    field="reason",
                    maximum_length=500,
                )
            ),
            "notes": (
                PurchaseReturnAPIService
                ._normalize_text(
                    payload.get(
                        "notes"
                    ),
                    field="notes",
                    maximum_length=1000,
                )
            ),
        }

    @staticmethod
    def get_purchase_return(
        *,
        organization,
        purchase_return_id,
    ):
        normalized_id = (
            PurchaseReturnAPIService
            ._normalize_identifier(
                purchase_return_id,
                field="purchase_return_id",
            )
        )

        purchase_return = (
            PurchaseReturnRepository
            .get_by_id(
                organization=organization,
                purchase_return_id=(
                    normalized_id
                ),
            )
        )

        if not purchase_return:
            raise LookupError(
                "Purchase return not found."
            )

        return purchase_return

    @staticmethod
    def create_purchase_return(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            PurchaseReturnAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                PurchaseReturnService
                .create_purchase_return(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                PurchaseReturnAPIStateError(
                    message=str(exc),
                    details={
                        "purchase_return": [
                            str(exc),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def confirm_purchase_return(
        *,
        user,
        organization,
        purchase_return_id,
    ):
        purchase_return = (
            PurchaseReturnAPIService
            .get_purchase_return(
                organization=organization,
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

        try:
            return (
                PurchaseReturnService
                .confirm_purchase_return(
                    user=user,
                    organization=organization,
                    purchase_return=(
                        purchase_return
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                PurchaseReturnAPIStateError(
                    message=str(exc),
                    details={
                        "purchase_return": [
                            str(exc),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def cancel_purchase_return(
        *,
        user,
        organization,
        purchase_return_id,
    ):
        purchase_return = (
            PurchaseReturnAPIService
            .get_purchase_return(
                organization=organization,
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

        try:
            return (
                PurchaseReturnService
                .cancel_purchase_return(
                    user=user,
                    organization=organization,
                    purchase_return=(
                        purchase_return
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                PurchaseReturnAPIStateError(
                    message=str(exc),
                    details={
                        "purchase_return": [
                            str(exc),
                        ],
                    },
                )
            ) from exc