from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.authorization.services import (
    AuthorizationService,
)

from apps.purchasing.models import (
    PurchaseReturnItem,
)

from apps.purchasing.repositories.purchase_return_repository import (
    PurchaseReturnRepository,
)
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)

from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)


class PurchaseReturnService:

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

        if (
            user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong to "
                "this organization."
            )

    @staticmethod
    def _generate_return_number():
        return (
            "PR-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _get_confirmed_returned_quantity(
        *,
        organization,
        purchase_order,
        product,
        exclude_purchase_return=None,
    ):
        returns = (
            PurchaseReturnRepository
            .list_by_purchase_order(
                organization=organization,
                purchase_order=purchase_order,
            )
        )

        returned_quantity = Decimal("0")

        for purchase_return in returns:
            if (
                exclude_purchase_return
                and purchase_return.id
                == exclude_purchase_return.id
            ):
                continue

            if (
                purchase_return.status
                != "CONFIRMED"
            ):
                continue

            for item in purchase_return.items:
                if (
                    item.product.id
                    == product.id
                ):
                    returned_quantity += (
                        item.quantity
                    )

        return returned_quantity

    @staticmethod
    def create_purchase_return(
        *,
        user,
        organization,
        purchase_order,
        vendor_bill,
        warehouse,
        items,
        return_date=None,
        reason="",
        notes="",
    ):
        PurchaseReturnService._check_permission(
            user,
            "purchase_returns.create",
        )

        PurchaseReturnService._check_organization(
            user,
            organization,
        )

        if not purchase_order:
            raise ValueError(
                "Purchase order is required."
            )

        if not vendor_bill:
            raise ValueError(
                "Vendor bill is required."
            )

        if not warehouse:
            raise ValueError(
                "Warehouse is required."
            )

        if (
            purchase_order.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Purchase order does not belong "
                "to this organization."
            )

        if (
            vendor_bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        if (
            warehouse.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Warehouse does not belong "
                "to this organization."
            )

        if (
            not vendor_bill.purchase_order
            or vendor_bill.purchase_order.id
            != purchase_order.id
        ):
            raise ValueError(
                "Vendor bill does not belong "
                "to this purchase order."
            )

        supplier = purchase_order.supplier

        if not supplier:
            raise ValueError(
                "Purchase order has no supplier."
            )

        if (
            vendor_bill.supplier.id
            != supplier.id
        ):
            raise ValueError(
                "Vendor bill supplier does not "
                "match purchase order supplier."
            )

        if not items:
            raise ValueError(
                "At least one return item "
                "is required."
            )

        return_items = []

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")
        total_amount = Decimal("0")

        seen_products = set()

        for item_data in items:
            product = item_data.get(
                "product"
            )


            if not product:
                raise ValueError(
                    "Product is required."
                )

            if (
                product.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Product does not belong "
                    "to this organization."
                )

            product_id = str(
                product.id
            )

            if product_id in seen_products:
                raise ValueError(
                    "Duplicate product in "
                    "purchase return."
                )

            seen_products.add(
                product_id
            )

            quantity = Decimal(
                str(
                    item_data.get(
                        "quantity",
                        0,
                    )
                )
            )

            if quantity <= 0:
                raise ValueError(
                    "Return quantity must be "
                    "greater than zero."
                )

            po_item = next(
                (
                    po_item
                    for po_item
                    in purchase_order.items
                    if po_item.product.id
                    == product.id
                ),
                None,
            )

            if not po_item:
                raise ValueError(
                    "Product does not belong "
                    "to this purchase order."
                )

            received_quantity = Decimal(
                str(
                    po_item.received_quantity
                )
            )

            already_returned = (
                PurchaseReturnService
                ._get_confirmed_returned_quantity(
                    organization=organization,
                    purchase_order=(
                        purchase_order
                    ),
                    product=product,
                )
            )

            returnable_quantity = (
                received_quantity
                - already_returned
            )

            if quantity > returnable_quantity:
                raise ValueError(
                    "Return quantity exceeds "
                    "available received quantity."
                )

            unit_price = Decimal(
                str(po_item.unit_price)
            )

            tax_rate = Decimal(
                str(po_item.tax_rate)
            )

            original_discount = Decimal(
                str(po_item.discount)
            )

            original_quantity = Decimal(
                str(po_item.quantity)
            )

            if original_quantity <= 0:
                raise ValueError(
                    "Purchase order item quantity "
                    "is invalid."
                )

            line_subtotal = (
                quantity
                * unit_price
            )

            line_discount = (
                original_discount
                * quantity
                / original_quantity
            )

            if line_discount > line_subtotal:
                raise ValueError(
                    "Return discount cannot exceed "
                    "return line value."
                )

            taxable_amount = (
                line_subtotal
                - line_discount
            )

            line_tax = (
                taxable_amount
                * tax_rate
                / Decimal("100")
            )

            line_total = (
                taxable_amount
                + line_tax
            )

            return_item = (
                PurchaseReturnItem(
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    discount=line_discount,
                    line_subtotal=(
                        line_subtotal
                    ),
                    line_tax=line_tax,
                    line_total=line_total,
                    reason=(
                        item_data.get(
                            "reason",
                            "",
                        ).strip()
                    ),
                )
            )

            return_items.append(
                return_item
            )

            subtotal += line_subtotal
            tax_amount += line_tax
            discount_amount += (
                line_discount
            )
            total_amount += line_total

        if total_amount <= 0:
            raise ValueError(
                "Purchase return total must "
                "be greater than zero."
            )

        if return_date is None:
            return_date = (
                datetime.utcnow()
            )

        return (
            PurchaseReturnRepository
            .create_purchase_return(
                organization=organization,
                return_number=(
                    PurchaseReturnService
                    ._generate_return_number()
                ),
                purchase_order=(
                    purchase_order
                ),
                vendor_bill=vendor_bill,
                supplier=supplier,
                warehouse=warehouse,
                return_date=return_date,
                items=return_items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=(
                    discount_amount
                ),
                total_amount=total_amount,
                reason=reason.strip(),
                notes=notes.strip(),
                created_by=user,
                status="DRAFT",
            )
        )

    @staticmethod
    def confirm_purchase_return(
        *,
        user,
        organization,
        purchase_return,
    ):
        PurchaseReturnService._check_permission(
            user,
            "purchase_returns.confirm",
        )

        PurchaseReturnService._check_organization(
            user,
            organization,
        )

        if not purchase_return:
            raise ValueError(
                "Purchase return is required."
            )

        if (
            purchase_return.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Purchase return does not belong "
                "to this organization."
            )

        if purchase_return.status != "DRAFT":
            raise ValueError(
                "Only draft purchase returns "
                "can be confirmed."
            )

        purchase_order = (
            purchase_return.purchase_order
        )

        if not purchase_order:
            raise ValueError(
                "Purchase return has no "
                "purchase order."
            )

        vendor_bill = (
            purchase_return.vendor_bill
        )

        if not vendor_bill:
            raise ValueError(
                "Purchase return has no "
                "vendor bill."
            )

        if (
            not vendor_bill.purchase_order
            or vendor_bill.purchase_order.id
            != purchase_order.id
        ):
            raise ValueError(
                "Vendor bill does not match "
                "purchase order."
            )

        if (
            purchase_return.supplier.id
            != purchase_order.supplier.id
        ):
            raise ValueError(
                "Purchase return supplier does "
                "not match purchase order."
            )

        warehouse = (
            purchase_return.warehouse
        )

        if not warehouse:
            raise ValueError(
                "Purchase return has no warehouse."
            )

        if not purchase_return.items:
            raise ValueError(
                "Purchase return has no items."
            )

        #
        # Phase 1:
        # Validate EVERYTHING before changing
        # any inventory.
        #
        inventory_updates = []

        for return_item in purchase_return.items:
            product = return_item.product

            po_item = next(
                (
                    item
                    for item
                    in purchase_order.items
                    if item.product.id
                    == product.id
                ),
                None,
            )

            if not po_item:
                raise ValueError(
                    "Purchase return contains "
                    "a product not found in "
                    "the purchase order."
                )

            already_returned = (
                PurchaseReturnService
                ._get_confirmed_returned_quantity(
                    organization=organization,
                    purchase_order=(
                        purchase_order
                    ),
                    product=product,
                    exclude_purchase_return=(
                        purchase_return
                    ),
                )
            )

            received_quantity = Decimal(
                str(
                    po_item.received_quantity
                )
            )

            if (
                already_returned
                + return_item.quantity
                > received_quantity
            ):
                raise ValueError(
                    "Return quantity exceeds "
                    "available received quantity."
                )

            if getattr(product,'item_type','goods')=='service':continue

            inventory = (
                InventoryRepository
                .get_by_product_and_warehouse(
                    organization=organization,
                    product=product,
                    warehouse=warehouse,
                )
            )

            if not inventory:
                raise ValueError(
                    f"Inventory not found for "
                    f"product {product.sku}."
                )

            quantity_before = Decimal(
                str(inventory.quantity)
            )

            reserved_before = Decimal(
                str(
                    inventory.reserved_quantity
                )
            )

            quantity_after = (
                quantity_before
                - return_item.quantity
            )

            if quantity_after < 0:
                raise ValueError(
                    f"Insufficient stock for "
                    f"product {product.sku}."
                )

            if (
                quantity_after
                < reserved_before
            ):
                raise ValueError(
                    f"Cannot return product "
                    f"{product.sku}; stock is "
                    f"reserved."
                )

            inventory_updates.append(
                {
                    "inventory":
                        inventory,
                    "return_item":
                        return_item,
                    "quantity_before":
                        quantity_before,
                    "quantity_after":
                        quantity_after,
                    "reserved_before":
                        reserved_before,
                }
            )

        #
        # Phase 2:
        # All validation passed.
        # Now perform inventory changes.
        #
        completed_updates = []

        try:
            for data in inventory_updates:
                inventory = data[
                    "inventory"
                ]

                return_item = data[
                    "return_item"
                ]

                inventory = (
                    InventoryRepository
                    .update_quantity(
                        inventory=inventory,
                        quantity=data[
                            "quantity_after"
                        ],
                    )
                )

                completed_updates.append(
                    data
                )

                StockMovementService.create_movement(
                    user=user,
                    organization=organization,
                    inventory=inventory,
                    movement_type=(
                        "PURCHASE_RETURN"
                    ),
                    quantity=(
                        -return_item.quantity
                    ),
                    quantity_before=data[
                        "quantity_before"
                    ],
                    quantity_after=data[
                        "quantity_after"
                    ],
                    reserved_before=data[
                        "reserved_before"
                    ],
                    reserved_after=(
                        inventory.reserved_quantity
                    ),
                    reference_type=(
                        "PURCHASE_RETURN"
                    ),
                    reference_id=(
                        purchase_return.return_number
                    ),
                    notes=(
                        "Purchase return "
                        f"{purchase_return.return_number}"
                    ),
                )

            purchase_return = (
                PurchaseReturnRepository
                .update_status(
                    purchase_return=(
                        purchase_return
                    ),
                    status="CONFIRMED",
                    confirmed_at=(
                        datetime.utcnow()
                    ),
                )
            )

        except Exception:
            #
            # Best-effort rollback because MongoEngine
            # operations here are not yet wrapped in
            # a MongoDB transaction.
            #
            for data in reversed(
                completed_updates
            ):
                try:
                    InventoryRepository.update_quantity(
                        inventory=data[
                            "inventory"
                        ],
                        quantity=data[
                            "quantity_before"
                        ],
                    )
                except Exception:
                    pass

            raise

        return purchase_return

    @staticmethod
    def cancel_purchase_return(
        *,
        user,
        organization,
        purchase_return,
    ):
        PurchaseReturnService._check_permission(
            user,
            "purchase_returns.cancel",
        )

        PurchaseReturnService._check_organization(
            user,
            organization,
        )

        if not purchase_return:
            raise ValueError(
                "Purchase return is required."
            )

        if (
            purchase_return.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Purchase return does not belong "
                "to this organization."
            )

        if (
            purchase_return.status
            == "CANCELLED"
        ):
            raise ValueError(
                "Purchase return is already "
                "cancelled."
            )

        if (
            purchase_return.status
            == "CONFIRMED"
        ):
            raise ValueError(
                "Confirmed purchase returns "
                "cannot be cancelled directly."
            )

        if (
            purchase_return.status
            != "DRAFT"
        ):
            raise ValueError(
                "Only draft purchase returns "
                "can be cancelled."
            )

        return (
            PurchaseReturnRepository
            .update_status(
                purchase_return=(
                    purchase_return
                ),
                status="CANCELLED",
                cancelled_at=(
                    datetime.utcnow()
                ),
            )
        )