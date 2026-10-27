from decimal import Decimal
from uuid import uuid4

from apps.authorization.services import AuthorizationService

from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)
from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)

from apps.purchasing.models import (
    GoodsReceiptItem,
)
from apps.purchasing.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class GoodsReceiptService:

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not AuthorizationService.has_permission(
            user,
            permission_code,
        ):
            raise PermissionError(
                f"Permission denied: {permission_code}"
            )

    @staticmethod
    def _check_organization(
        user,
        organization,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

    @staticmethod
    def _generate_grn_number():
        return (
            "GRN-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def receive_goods(
        *,
        user,
        organization,
        purchase_order,
        warehouse,
        raw_items,
        notes="",
    ):
        """
        Receive goods against a confirmed PO.
        """

        GoodsReceiptService._check_permission(
            user,
            "goods_receipts.create",
        )

        GoodsReceiptService._check_organization(
            user,
            organization,
        )

        if not purchase_order:
            raise ValueError(
                "Purchase order is required."
            )

        if purchase_order.organization.id != organization.id:
            raise PermissionError(
                "Purchase order does not belong to this organization."
            )

        if purchase_order.status not in {
            "CONFIRMED",
            "PARTIALLY_RECEIVED",
        }:
            raise ValueError(
                "Goods can only be received against "
                "confirmed or partially received purchase orders."
            )

        if not warehouse:
            raise ValueError(
                "Warehouse is required."
            )

        if warehouse.organization.id != organization.id:
            raise PermissionError(
                "Warehouse does not belong to this organization."
            )

        if not warehouse.is_active:
            raise ValueError(
                "Inactive warehouse cannot receive goods."
            )

        if not raw_items:
            raise ValueError(
                "Goods receipt must contain at least one item."
            )

        po_items_by_product = {
            str(item.product.id): item
            for item in purchase_order.items
        }

        receipt_items = []
        receipt_updates = []

        for raw_item in raw_items:

            product = raw_item.get(
                "product"
            )

            if not product:
                raise ValueError(
                    "Product is required."
                )

            if product.organization.id != organization.id:
                raise PermissionError(
                    "Product does not belong to this organization."
                )

            product_id = str(
                product.id
            )

            po_item = po_items_by_product.get(
                product_id
            )

            if not po_item:
                raise ValueError(
                    f"Product {product.sku} "
                    "is not part of this purchase order."
                )

            quantity_received = Decimal(
                str(
                    raw_item.get(
                        "quantity_received",
                        0,
                    )
                )
            )

            if quantity_received <= 0:
                raise ValueError(
                    "Received quantity must be greater than zero."
                )

            remaining_quantity = (
                po_item.quantity
                - po_item.received_quantity
            )

            if quantity_received > remaining_quantity:
                raise ValueError(
                    f"Cannot receive more than remaining "
                    f"quantity for product {product.sku}."
                )

            receipt_items.append(
                GoodsReceiptItem(
                    product=product,
                    quantity_received=quantity_received,
                )
            )

            receipt_updates.append(
                {
                    "product": product,
                    "po_item": po_item,
                    "quantity_received":
                        quantity_received,
                }
            )

        grn_number = (
            GoodsReceiptService
            ._generate_grn_number()
        )

        # -------------------------------------
        # UPDATE INVENTORY + STOCK MOVEMENTS
        # -------------------------------------

        for update in receipt_updates:

            product = update["product"]

            quantity_received = update[
                "quantity_received"
            ]

            inventory = (
                InventoryRepository
                .get_by_product_and_warehouse(
                    organization=organization,
                    product=product,
                    warehouse=warehouse,
                )
            )

            if not inventory:
                inventory = (
                    InventoryRepository
                    .create_inventory(
                        organization=organization,
                        product=product,
                        warehouse=warehouse,
                        quantity=0,
                        reserved_quantity=0,
                    )
                )

            quantity_before = (
                inventory.quantity
            )

            reserved_before = (
                inventory.reserved_quantity
            )

            quantity_after = (
                quantity_before
                + quantity_received
            )

            inventory = (
                InventoryRepository
                .update_quantity(
                    inventory=inventory,
                    quantity=quantity_after,
                )
            )

            StockMovementService.create_movement(
                user=user,
                organization=organization,
                inventory=inventory,
                movement_type="STOCK_IN",
                quantity=quantity_received,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                reserved_before=reserved_before,
                reserved_after=(
                    inventory.reserved_quantity
                ),
                reference_type="GOODS_RECEIPT",
                reference_id=grn_number,
                notes=notes,
            )

        # -------------------------------------
        # UPDATE PO RECEIVED QUANTITIES
        # -------------------------------------

        for update in receipt_updates:
            po_item = update["po_item"]

            po_item.received_quantity += (
                update["quantity_received"]
            )

        all_received = all(
            item.received_quantity
            >= item.quantity
            for item in purchase_order.items
        )

        if all_received:
            new_status = "RECEIVED"
        else:
            new_status = "PARTIALLY_RECEIVED"

        purchase_order = (
            PurchaseOrderRepository
            .update_received_quantities(
                purchase_order=purchase_order,
                items=purchase_order.items,
                status=new_status,
            )
        )

        # -------------------------------------
        # CREATE GRN
        # -------------------------------------

        goods_receipt = (
            GoodsReceiptRepository
            .create_goods_receipt(
                organization=organization,
                grn_number=grn_number,
                purchase_order=purchase_order,
                supplier=purchase_order.supplier,
                warehouse=warehouse,
                items=receipt_items,
                notes=notes.strip(),
                received_by=user,
            )
        )

        return goods_receipt