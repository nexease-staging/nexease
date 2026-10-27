from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.authorization.services import AuthorizationService
from apps.purchasing.models import PurchaseOrderItem
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class PurchaseOrderService:

    VALID_STATUSES = {
        "DRAFT",
        "CONFIRMED",
        "PARTIALLY_RECEIVED",
        "RECEIVED",
        "CANCELLED",
    }

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
    def _validate_supplier(
        supplier,
        organization,
    ):
        if not supplier:
            raise ValueError(
                "Supplier is required."
            )

        if supplier.organization.id != organization.id:
            raise PermissionError(
                "Supplier does not belong to this organization."
            )

        if not supplier.is_active:
            raise ValueError(
                "Inactive supplier cannot be used."
            )

    @staticmethod
    def _generate_po_number():
        return (
            "PO-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _build_items(
        *,
        organization,
        raw_items,
    ):
        """
        Validate PO lines and calculate
        per-line amounts.
        """

        if not raw_items:
            raise ValueError(
                "Purchase order must contain at least one item."
            )

        product_ids = set()
        items = []

        subtotal_total = Decimal("0")
        tax_total = Decimal("0")
        discount_total = Decimal("0")

        for raw_item in raw_items:

            product = raw_item.get(
                "product"
            )

            if not product:
                raise ValueError(
                    "Product is required for every item."
                )

            if product.organization.id != organization.id:
                raise PermissionError(
                    "Product does not belong to this organization."
                )

            if not product.is_active:
                raise ValueError(
                    f"Inactive product cannot be ordered: "
                    f"{product.name}"
                )

            product_id = str(
                product.id
            )

            if product_id in product_ids:
                raise ValueError(
                    f"Duplicate product in purchase order: "
                    f"{product.sku}"
                )

            product_ids.add(
                product_id
            )

            quantity = Decimal(
                str(
                    raw_item.get(
                        "quantity",
                        0,
                    )
                )
            )

            unit_price = Decimal(
                str(
                    raw_item.get(
                        "unit_price",
                        0,
                    )
                )
            )

            tax_rate = Decimal(
                str(
                    raw_item.get(
                        "tax_rate",
                        0,
                    )
                )
            )

            discount = Decimal(
                str(
                    raw_item.get(
                        "discount",
                        0,
                    )
                )
            )

            if quantity <= 0:
                raise ValueError(
                    "Item quantity must be greater than zero."
                )

            if unit_price < 0:
                raise ValueError(
                    "Unit price cannot be negative."
                )

            if tax_rate < 0:
                raise ValueError(
                    "Tax rate cannot be negative."
                )

            if discount < 0:
                raise ValueError(
                    "Discount cannot be negative."
                )

            line_base = (
                quantity
                * unit_price
            )

            if discount > line_base:
                raise ValueError(
                    "Discount cannot exceed line value."
                )

            subtotal = (
                line_base
                - discount
            )

            tax_amount = (
                subtotal
                * tax_rate
                / Decimal("100")
            )

            total = (
                subtotal
                + tax_amount
            )

            item = PurchaseOrderItem(
                product=product,
                quantity=quantity,
                received_quantity=Decimal("0"),
                unit_price=unit_price,
                tax_rate=tax_rate,
                discount=discount,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total=total,
            )

            items.append(
                item
            )

            subtotal_total += subtotal
            tax_total += tax_amount
            discount_total += discount

        total_amount = (
            subtotal_total
            + tax_total
        )

        return {
            "items": items,
            "subtotal": subtotal_total,
            "tax_amount": tax_total,
            "discount_amount": discount_total,
            "total_amount": total_amount,
        }

    @staticmethod
    def create_purchase_order(
        *,
        user,
        organization,
        supplier,
        order_date,
        expected_delivery_date,
        raw_items,
        notes="",
    ):
        PurchaseOrderService._check_permission(
            user,
            "purchase_orders.create",
        )

        PurchaseOrderService._check_organization(
            user,
            organization,
        )

        PurchaseOrderService._validate_supplier(
            supplier,
            organization,
        )

        calculated = PurchaseOrderService._build_items(
            organization=organization,
            raw_items=raw_items,
        )

        po_number = (
            PurchaseOrderService
            ._generate_po_number()
        )

        return PurchaseOrderRepository.create_purchase_order(
            organization=organization,
            po_number=po_number,
            supplier=supplier,
            order_date=order_date,
            expected_delivery_date=(
                expected_delivery_date
            ),
            items=calculated["items"],
            subtotal=calculated["subtotal"],
            tax_amount=calculated["tax_amount"],
            discount_amount=calculated[
                "discount_amount"
            ],
            total_amount=calculated["total_amount"],
            notes=notes.strip(),
            created_by=user,
            status="DRAFT",
        )

    @staticmethod
    def get_purchase_order(
        *,
        user,
        organization,
        purchase_order_id,
    ):
        PurchaseOrderService._check_permission(
            user,
            "purchase_orders.read",
        )

        PurchaseOrderService._check_organization(
            user,
            organization,
        )

        purchase_order = (
            PurchaseOrderRepository.get_by_id(
                organization=organization,
                purchase_order_id=purchase_order_id,
            )
        )

        if not purchase_order:
            raise ValueError(
                "Purchase order not found."
            )

        return purchase_order

    @staticmethod
    def list_purchase_orders(
        *,
        user,
        organization,
        status=None,
    ):
        PurchaseOrderService._check_permission(
            user,
            "purchase_orders.read",
        )

        PurchaseOrderService._check_organization(
            user,
            organization,
        )

        if status:
            status = status.upper()

            if status not in (
                PurchaseOrderService.VALID_STATUSES
            ):
                raise ValueError(
                    "Invalid purchase order status."
                )

            return PurchaseOrderRepository.list_by_status(
                organization=organization,
                status=status,
            )

        return (
            PurchaseOrderRepository
            .list_by_organization(
                organization=organization,
            )
        )

    @staticmethod
    def update_purchase_order(
        *,
        user,
        organization,
        purchase_order_id,
        supplier=None,
        order_date=None,
        expected_delivery_date=None,
        raw_items=None,
        notes=None,
    ):
        PurchaseOrderService._check_permission(
            user,
            "purchase_orders.update",
        )

        PurchaseOrderService._check_organization(
            user,
            organization,
        )

        purchase_order = (
            PurchaseOrderRepository.get_by_id(
                organization=organization,
                purchase_order_id=purchase_order_id,
            )
        )

        if not purchase_order:
            raise ValueError(
                "Purchase order not found."
            )

        if purchase_order.status != "DRAFT":
            raise ValueError(
                "Only draft purchase orders can be updated."
            )

        if supplier is not None:
            PurchaseOrderService._validate_supplier(
                supplier,
                organization,
            )

        calculated = None

        if raw_items is not None:
            calculated = (
                PurchaseOrderService._build_items(
                    organization=organization,
                    raw_items=raw_items,
                )
            )

        return (
            PurchaseOrderRepository
            .update_purchase_order(
                purchase_order=purchase_order,
                supplier=supplier,
                order_date=order_date,
                expected_delivery_date=(
                    expected_delivery_date
                ),
                items=(
                    calculated["items"]
                    if calculated
                    else None
                ),
                subtotal=(
                    calculated["subtotal"]
                    if calculated
                    else None
                ),
                tax_amount=(
                    calculated["tax_amount"]
                    if calculated
                    else None
                ),
                discount_amount=(
                    calculated["discount_amount"]
                    if calculated
                    else None
                ),
                total_amount=(
                    calculated["total_amount"]
                    if calculated
                    else None
                ),
                notes=(
                    notes.strip()
                    if notes is not None
                    else None
                ),
            )
        )

    @staticmethod
    def confirm_purchase_order(
        *,
        user,
        organization,
        purchase_order_id,
    ):
        PurchaseOrderService._check_permission(
            user,
            "purchase_orders.update",
        )

        PurchaseOrderService._check_organization(
            user,
            organization,
        )

        purchase_order = (
            PurchaseOrderRepository.get_by_id(
                organization=organization,
                purchase_order_id=purchase_order_id,
            )
        )

        if not purchase_order:
            raise ValueError(
                "Purchase order not found."
            )

        if purchase_order.status != "DRAFT":
            raise ValueError(
                "Only draft purchase orders can be confirmed."
            )

        if not purchase_order.items:
            raise ValueError(
                "Purchase order has no items."
            )

        return PurchaseOrderRepository.update_status(
            purchase_order=purchase_order,
            status="CONFIRMED",
            confirmed_at=datetime.utcnow(),
        )

    @staticmethod
    def cancel_purchase_order(
        *,
        user,
        organization,
        purchase_order_id,
    ):
        PurchaseOrderService._check_permission(
            user,
            "purchase_orders.cancel",
        )

        PurchaseOrderService._check_organization(
            user,
            organization,
        )

        purchase_order = (
            PurchaseOrderRepository.get_by_id(
                organization=organization,
                purchase_order_id=purchase_order_id,
            )
        )

        if not purchase_order:
            raise ValueError(
                "Purchase order not found."
            )

        if purchase_order.status == "CANCELLED":
            raise ValueError(
                "Purchase order is already cancelled."
            )

        if purchase_order.status in {
            "PARTIALLY_RECEIVED",
            "RECEIVED",
        }:
            raise ValueError(
                "Received purchase orders cannot be cancelled."
            )

        return PurchaseOrderRepository.update_status(
            purchase_order=purchase_order,
            status="CANCELLED",
            cancelled_at=datetime.utcnow(),
        )