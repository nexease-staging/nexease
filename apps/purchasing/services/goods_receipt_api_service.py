from datetime import datetime
from decimal import Decimal, InvalidOperation

from bson import ObjectId

from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)
from apps.purchasing.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from apps.purchasing.services.goods_receipt_service import (
    GoodsReceiptService,
)


class GoodsReceiptAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Validation failed.",
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class GoodsReceiptAPIService:

    @staticmethod
    def _field_error(
        field_name,
        message,
    ):
        raise GoodsReceiptAPIValidationError(
            details={
                field_name: [
                    message,
                ],
            },
        )

    @staticmethod
    def _validate_payload(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise GoodsReceiptAPIValidationError(
                details={
                    "body": [
                        (
                            "JSON body must be "
                            "an object."
                        ),
                    ],
                },
            )

        return payload

    @staticmethod
    def _parse_object_id(
        value,
        *,
        field_name,
    ):
        if not isinstance(
            value,
            str,
        ) or not value.strip():

            GoodsReceiptAPIService._field_error(
                field_name,
                "This field is required.",
            )

        value = value.strip()

        if not ObjectId.is_valid(value):
            GoodsReceiptAPIService._field_error(
                field_name,
                "Enter a valid identifier.",
            )

        return ObjectId(value)

    @staticmethod
    def _parse_quantity(
        value,
        *,
        index,
    ):
        try:
            quantity = Decimal(
                str(value)
            )

        except (
            InvalidOperation,
            ValueError,
            TypeError,
        ):
            raise GoodsReceiptAPIValidationError(
                details={
                    f"items[{index}].quantity_received": [
                        (
                            "Enter a valid quantity."
                        ),
                    ],
                },
            )

        if quantity <= 0:
            raise GoodsReceiptAPIValidationError(
                details={
                    f"items[{index}].quantity_received": [
                        (
                            "Received quantity must "
                            "be greater than zero."
                        ),
                    ],
                },
            )

        return quantity

    @staticmethod
    def receive_goods(
        *,
        user,
        organization,
        payload,
    ):
        payload = (
            GoodsReceiptAPIService
            ._validate_payload(
                payload,
            )
        )

        purchase_order_id = (
            GoodsReceiptAPIService
            ._parse_object_id(
                payload.get(
                    "purchase_order_id",
                ),
                field_name=(
                    "purchase_order_id"
                ),
            )
        )

        warehouse_id = (
            GoodsReceiptAPIService
            ._parse_object_id(
                payload.get(
                    "warehouse_id",
                ),
                field_name="warehouse_id",
            )
        )

        raw_items = payload.get(
            "items",
        )

        if not isinstance(
            raw_items,
            list,
        ) or not raw_items:

            raise GoodsReceiptAPIValidationError(
                details={
                    "items": [
                        (
                            "At least one receipt "
                            "item is required."
                        ),
                    ],
                },
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
            raise LookupError(
                "Purchase order not found."
            )

        warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if not warehouse:
            raise LookupError(
                "Warehouse not found."
            )

        products = []

        normalized_items = []

        for index, raw_item in enumerate(
            raw_items
        ):
            if not isinstance(
                raw_item,
                dict,
            ):
                raise GoodsReceiptAPIValidationError(
                    details={
                        f"items[{index}]": [
                            (
                                "Each item must be "
                                "an object."
                            ),
                        ],
                    },
                )

            product_id = (
                GoodsReceiptAPIService
                ._parse_object_id(
                    raw_item.get(
                        "product_id",
                    ),
                    field_name=(
                        f"items[{index}].product_id"
                    ),
                )
            )

            quantity_received = (
                GoodsReceiptAPIService
                ._parse_quantity(
                    raw_item.get(
                        "quantity_received",
                    ),
                    index=index,
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
                raise LookupError(
                    "Product not found."
                )

            products.append(product)

            normalized_items.append(
                {
                    "product": product,
                    "quantity_received":
                        quantity_received,
                },
            )

        goods_receipt = (
            GoodsReceiptService
            .receive_goods(
                user=user,
                organization=organization,
                purchase_order=purchase_order,
                warehouse=warehouse,
                raw_items=normalized_items,
                notes=(
                    str(
                        payload.get(
                            "notes",
                            "",
                        )
                        or ""
                    ).strip()
                ),
            )
        )

        return goods_receipt

    @staticmethod
    def get_goods_receipt(
        *,
        organization,
        goods_receipt_id,
    ):
        goods_receipt_id = (
            GoodsReceiptAPIService
            ._parse_object_id(
                goods_receipt_id,
                field_name="goods_receipt_id",
            )
        )

        goods_receipt = (
            GoodsReceiptRepository
            .get_by_id(
                organization=organization,
                goods_receipt_id=(
                    goods_receipt_id
                ),
            )
        )

        if not goods_receipt:
            raise LookupError(
                "Goods receipt not found."
            )

        return goods_receipt

    @staticmethod
    def list_goods_receipts(
        *,
        organization,
    ):
        return (
            GoodsReceiptRepository
            .list_by_organization(
                organization=organization,
            )
        )