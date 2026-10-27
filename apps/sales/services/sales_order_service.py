from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.authorization.services import (
    AuthorizationService,
)

from apps.sales.models import (
    SalesOrderItem,
)

from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)

from apps.inventory.services.inventory_service import (
    InventoryService,
)
from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)
class SalesOrderService:

    VALID_STATUSES = {
        "DRAFT",
        "CONFIRMED",
        "PARTIALLY_FULFILLED",
        "FULFILLED",
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
    def _generate_so_number():
        return (
            "SO-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _to_decimal(
        value,
        field_name,
    ):
        try:
            return Decimal(
                str(value)
            )
        except Exception:
            raise ValueError(
                f"Invalid {field_name}."
            )

    @staticmethod
    def _build_items(
        *,
        organization,
        raw_items,
    ):
        if not raw_items:
            raise ValueError(
                "Sales order must contain at least one item."
            )

        items = []
        product_ids = set()

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")
        total_amount = Decimal("0")

        for raw_item in raw_items:

            product = raw_item.get(
                "product"
            )

            if not product:
                raise ValueError(
                    "Product is required."
                )

            if (
                not product.organization
                or product.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Product does not belong to this organization."
                )

            product_id = str(
                product.id
            )

            if product_id in product_ids:
                raise ValueError(
                    "Duplicate product in sales order."
                )

            product_ids.add(
                product_id
            )

            quantity = (
                SalesOrderService
                ._to_decimal(
                    raw_item.get(
                        "quantity"
                    ),
                    "quantity",
                )
            )

            unit_price = (
                SalesOrderService
                ._to_decimal(
                    raw_item.get(
                        "unit_price"
                    ),
                    "unit price",
                )
            )

            tax_rate = (
                SalesOrderService
                ._to_decimal(
                    raw_item.get(
                        "tax_rate",
                        0,
                    ),
                    "tax rate",
                )
            )

            discount = (
                SalesOrderService
                ._to_decimal(
                    raw_item.get(
                        "discount",
                        0,
                    ),
                    "discount",
                )
            )

            if quantity <= 0:
                raise ValueError(
                    "Quantity must be greater than zero."
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

            line_subtotal = (
                quantity
                * unit_price
            )

            if discount > line_subtotal:
                raise ValueError(
                    "Discount cannot exceed line subtotal."
                )

            taxable_amount = (
                line_subtotal
                - discount
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

            item = SalesOrderItem(
                product=product,
                quantity=quantity,
                fulfilled_quantity=Decimal("0"),
                unit_price=unit_price,
                tax_rate=tax_rate,
                discount=discount,
                line_subtotal=line_subtotal,
                line_tax=line_tax,
                line_total=line_total,
            )

            items.append(
                item
            )

            subtotal += line_subtotal
            tax_amount += line_tax
            discount_amount += discount
            total_amount += line_total

        return {
            "items": items,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
        }

    @staticmethod
    def create_sales_order(
        *,
        user,
        organization,
        customer,
        warehouse,
        order_date,
        expected_delivery_date=None,
        raw_items,
        notes="",
    ):
        SalesOrderService._check_permission(
            user,
            "sales_orders.create",
        )

        SalesOrderService._check_organization(
            user,
            organization,
        )

        if not customer:
            raise ValueError(
                "Customer is required."
            )

        if (
            not customer.organization
            or customer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Customer does not belong to this organization."
            )

        if not customer.is_active:
            raise ValueError(
                "Customer is inactive."
            )

        if not warehouse:
            raise ValueError(
                "Warehouse is required."
            )

        if (
            not warehouse.organization
            or warehouse.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Warehouse does not belong to this organization."
            )

        if not warehouse.is_active:
            raise ValueError(
                "Warehouse is inactive."
            )

        calculated = (
            SalesOrderService._build_items(
                organization=organization,
                raw_items=raw_items,
            )
        )

        so_number = (
            SalesOrderService
            ._generate_so_number()
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
                notes=notes.strip(),
                created_by=user,
                status="DRAFT",
            )
        )

    @staticmethod
    def get_sales_order(
        *,
        user,
        organization,
        sales_order_id,
    ):
        SalesOrderService._check_permission(
            user,
            "sales_orders.read",
        )

        SalesOrderService._check_organization(
            user,
            organization,
        )

        sales_order = (
            SalesOrderRepository.get_by_id(
                organization=organization,
                sales_order_id=sales_order_id,
            )
        )

        if not sales_order:
            raise ValueError(
                "Sales order not found."
            )

        return sales_order

    @staticmethod
    def list_sales_orders(
        *,
        user,
        organization,
        status=None,
    ):
        SalesOrderService._check_permission(
            user,
            "sales_orders.read",
        )

        SalesOrderService._check_organization(
            user,
            organization,
        )

        if status is None:
            return (
                SalesOrderRepository
                .list_by_organization(
                    organization=organization,
                )
            )

        status = status.strip().upper()

        if status not in (
            SalesOrderService
            .VALID_STATUSES
        ):
            raise ValueError(
                "Invalid sales order status."
            )

        return (
            SalesOrderRepository
            .list_by_status(
                organization=organization,
                status=status,
            )
        )

    @staticmethod
    def update_sales_order(
        *,
        user,
        organization,
        sales_order_id,
        customer=None,
        warehouse=None,
        order_date=None,
        expected_delivery_date=None,
        raw_items=None,
        notes=None,
    ):
        SalesOrderService._check_permission(
            user,
            "sales_orders.update",
        )

        SalesOrderService._check_organization(
            user,
            organization,
        )

        sales_order = (
            SalesOrderRepository.get_by_id(
                organization=organization,
                sales_order_id=sales_order_id,
            )
        )

        if not sales_order:
            raise ValueError(
                "Sales order not found."
            )

        if sales_order.status != "DRAFT":
            raise ValueError(
                "Only draft sales orders can be edited."
            )

        if customer is not None:
            if (
                not customer.organization
                or customer.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Customer does not belong "
                    "to this organization."
                )

            if not customer.is_active:
                raise ValueError(
                    "Customer is inactive."
                )

        if warehouse is not None:
            if (
                not warehouse.organization
                or warehouse.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Warehouse does not belong "
                    "to this organization."
                )

            if not warehouse.is_active:
                raise ValueError(
                    "Warehouse is inactive."
                )

        items = None
        subtotal = None
        tax_amount = None
        discount_amount = None
        total_amount = None

        if raw_items is not None:
            calculated = (
                SalesOrderService._build_items(
                    organization=organization,
                    raw_items=raw_items,
                )
            )

            items = calculated["items"]
            subtotal = calculated["subtotal"]
            tax_amount = calculated[
                "tax_amount"
            ]
            discount_amount = calculated[
                "discount_amount"
            ]
            total_amount = calculated[
                "total_amount"
            ]

        return (
            SalesOrderRepository
            .update_sales_order(
                sales_order=sales_order,
                customer=customer,
                warehouse=warehouse,
                order_date=order_date,
                expected_delivery_date=(
                    expected_delivery_date
                ),
                items=items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=(
                    discount_amount
                ),
                total_amount=total_amount,
                notes=(
                    notes.strip()
                    if notes is not None
                    else None
                ),
            )
        )

    @staticmethod
    def confirm_sales_order(
        *,
        user,
        organization,
        sales_order_id,
    ):
        """
        Confirm a draft sales order and reserve
        the required inventory.

        Physical inventory is NOT reduced here.
        Only reserved_quantity is increased.
        """

        SalesOrderService._check_permission(
            user,
            "sales_orders.update",
        )

        SalesOrderService._check_organization(
            user,
            organization,
        )

        sales_order = (
            SalesOrderRepository.get_by_id(
                organization=organization,
                sales_order_id=sales_order_id,
            )
        )

        if not sales_order:
            raise ValueError(
                "Sales order not found."
            )

        if sales_order.status != "DRAFT":
            raise ValueError(
                "Only draft sales orders can be confirmed."
            )

        if not sales_order.customer:
            raise ValueError(
                "Sales order has no customer."
            )

        if (
            sales_order.customer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Customer does not belong to this organization."
            )

        if not sales_order.customer.is_active:
            raise ValueError(
                "Inactive customer cannot be used."
            )

        if not sales_order.warehouse:
            raise ValueError(
                "Sales order has no warehouse."
            )

        if (
            sales_order.warehouse.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Warehouse does not belong to this organization."
            )

        if not sales_order.warehouse.is_active:
            raise ValueError(
                "Inactive warehouse cannot fulfill sales orders."
            )

        if not sales_order.items:
            raise ValueError(
                "Sales order has no items."
            )

        # -------------------------------------------------
        # STEP 1: VALIDATE ALL LINES BEFORE RESERVING
        # -------------------------------------------------

        reservations = []

        for item in sales_order.items:

            product = item.product

            if not product:
                raise ValueError(
                    "Sales order item has no product."
                )

            if (
                product.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Product does not belong to this organization."
                )

            if not product.is_active:
                raise ValueError(
                    f"Inactive product cannot be reserved: "
                    f"{product.sku}"
                )

            inventory = (
                InventoryRepository
                .get_by_product_and_warehouse(
                    organization=organization,
                    product=product,
                    warehouse=sales_order.warehouse,
                )
            )

            if not inventory:
                raise ValueError(
                    f"Inventory not found for product "
                    f"{product.sku} in warehouse "
                    f"{sales_order.warehouse.code}."
                )

            available_quantity = (
                inventory.quantity
                - inventory.reserved_quantity
            )

            quantity_to_reserve = (
                item.quantity
                - item.fulfilled_quantity
            )

            if quantity_to_reserve <= 0:
                raise ValueError(
                    f"Invalid reservation quantity "
                    f"for product {product.sku}."
                )

            if (
                quantity_to_reserve
                > available_quantity
            ):
                raise ValueError(
                    f"Insufficient available inventory "
                    f"for product {product.sku}. "
                    f"Required: {quantity_to_reserve}, "
                    f"Available: {available_quantity}."
                )

            reservations.append(
                {
                    "inventory": inventory,
                    "product": product,
                    "quantity": quantity_to_reserve,
                }
            )

        # -------------------------------------------------
        # STEP 2: RESERVE INVENTORY
        # -------------------------------------------------

        completed_reservations = []

        try:
            for reservation in reservations:

                InventoryService.reserve_quantity(
                    user=user,
                    organization=organization,
                    inventory_id=str(
                        reservation[
                            "inventory"
                        ].id
                    ),
                    quantity=reservation[
                        "quantity"
                    ],
                    reference_type="SALES_ORDER",
                    reference_id=(
                        sales_order.so_number
                    ),
                    notes=(
                        f"Inventory reserved for "
                        f"sales order "
                        f"{sales_order.so_number}"
                    ),
                )

                completed_reservations.append(
                    reservation
                )

        except Exception:

            # Best-effort rollback if one line fails
            # after previous lines were reserved.
            for reservation in reversed(
                completed_reservations
            ):
                try:
                    InventoryService.release_reserved_quantity(
                        user=user,
                        organization=organization,
                        inventory_id=str(
                            reservation[
                                "inventory"
                            ].id
                        ),
                        quantity=reservation[
                            "quantity"
                        ],
                        reference_type="SALES_ORDER",
                        reference_id=(
                            sales_order.so_number
                        ),
                        notes=(
                            "Reservation rollback for "
                            f"sales order "
                            f"{sales_order.so_number}"
                        ),
                    )

                except Exception:
                    pass

            raise

        # -------------------------------------------------
        # STEP 3: CONFIRM SALES ORDER
        # -------------------------------------------------

        return (
            SalesOrderRepository.update_status(
                sales_order=sales_order,
                status="CONFIRMED",
                confirmed_at=datetime.utcnow(),
            )
        )

    @staticmethod
    def cancel_sales_order(
        *,
        user,
        organization,
        sales_order_id,
    ):
        """
        Cancel a sales order.

        DRAFT:
            Cancel directly.

        CONFIRMED:
            Release all inventory reservations
            and then cancel the order.
        """

        SalesOrderService._check_permission(
            user,
            "sales_orders.cancel",
        )

        SalesOrderService._check_organization(
            user,
            organization,
        )

        sales_order = (
            SalesOrderRepository.get_by_id(
                organization=organization,
                sales_order_id=sales_order_id,
            )
        )

        if not sales_order:
            raise ValueError(
                "Sales order not found."
            )

        if sales_order.status == "CANCELLED":
            raise ValueError(
                "Sales order is already cancelled."
            )

        if sales_order.status == "FULFILLED":
            raise ValueError(
                "Fulfilled sales order cannot be cancelled."
            )

        if (
            sales_order.status
            == "PARTIALLY_FULFILLED"
        ):
            raise ValueError(
                "Partially fulfilled sales order "
                "cancellation is not supported yet."
            )

        # DRAFT has no reservation to release.
        if sales_order.status == "DRAFT":
            return (
                SalesOrderRepository.update_status(
                    sales_order=sales_order,
                    status="CANCELLED",
                    cancelled_at=datetime.utcnow(),
                )
            )

        if sales_order.status != "CONFIRMED":
            raise ValueError(
                "Sales order cannot be cancelled "
                "from its current status."
            )

        releases = []

        # Validate everything BEFORE changing inventory.
        for item in sales_order.items:
            quantity_to_release = (
                item.quantity
                - item.fulfilled_quantity
            )

            if quantity_to_release <= 0:
                continue

            inventory = (
                InventoryRepository
                .get_by_product_and_warehouse(
                    organization=organization,
                    product=item.product,
                    warehouse=sales_order.warehouse,
                )
            )

            if not inventory:
                raise ValueError(
                    f"Inventory not found for product "
                    f"{item.product.sku}."
                )

            if (
                inventory.reserved_quantity
                < quantity_to_release
            ):
                raise ValueError(
                    f"Reserved inventory is insufficient "
                    f"for cancellation of product "
                    f"{item.product.sku}. "
                    f"Required release: "
                    f"{quantity_to_release}, "
                    f"Reserved: "
                    f"{inventory.reserved_quantity}."
                )

            releases.append(
                {
                    "inventory": inventory,
                    "quantity":
                        quantity_to_release,
                }
            )

        completed_releases = []

        try:
            for release in releases:
                InventoryService.release_reserved_quantity(
                    user=user,
                    organization=organization,
                    inventory_id=str(
                        release["inventory"].id
                    ),
                    quantity=release[
                        "quantity"
                    ],
                    reference_type="SALES_ORDER",
                    reference_id=(
                        sales_order.so_number
                    ),
                    notes=(
                        "Reservation released because "
                        f"sales order "
                        f"{sales_order.so_number} "
                        "was cancelled"
                    ),
                )

                completed_releases.append(
                    release
                )

        except Exception:
            # Best-effort rollback:
            # re-reserve anything already released.
            for release in reversed(
                completed_releases
            ):
                try:
                    InventoryService.reserve_quantity(
                        user=user,
                        organization=organization,
                        inventory_id=str(
                            release[
                                "inventory"
                            ].id
                        ),
                        quantity=release[
                            "quantity"
                        ],
                        reference_type="SALES_ORDER",
                        reference_id=(
                            sales_order.so_number
                        ),
                        notes=(
                            "Cancellation rollback for "
                            f"sales order "
                            f"{sales_order.so_number}"
                        ),
                    )

                except Exception:
                    pass

            raise

        return (
            SalesOrderRepository.update_status(
                sales_order=sales_order,
                status="CANCELLED",
                cancelled_at=datetime.utcnow(),
            )
        )

    @staticmethod
    def fulfill_sales_order(
        *,
        user,
        organization,
        sales_order_id,
        raw_items,
        notes="",
    ):
        """
        Partially or fully fulfil a sales order.

        Fulfilment:
        - reduces physical inventory
        - reduces reserved inventory
        - increases fulfilled quantity
        - creates STOCK_OUT movement
        """

        SalesOrderService._check_permission(
            user,
            "sales_orders.fulfill",
        )

        SalesOrderService._check_organization(
            user,
            organization,
        )

        sales_order = (
            SalesOrderRepository.get_by_id(
                organization=organization,
                sales_order_id=sales_order_id,
            )
        )

        if not sales_order:
            raise ValueError(
                "Sales order not found."
            )

        if sales_order.status not in {
            "CONFIRMED",
            "PARTIALLY_FULFILLED",
        }:
            raise ValueError(
                "Only confirmed or partially fulfilled "
                "sales orders can be fulfilled."
            )

        if not raw_items:
            raise ValueError(
                "Fulfilment must contain at least one item."
            )

        if not isinstance(
            raw_items,
            list,
        ):
            raise ValueError(
                "Fulfilment items must be a list."
            )

        # ---------------------------------------------
        # MAP SALES ORDER ITEMS BY PRODUCT
        # ---------------------------------------------

        order_items = {
            str(item.product.id): item
            for item in sales_order.items
        }

        product_ids = set()

        fulfilments = []

        # ---------------------------------------------
        # VALIDATE EVERYTHING FIRST
        # ---------------------------------------------

        for raw_item in raw_items:

            product = raw_item.get(
                "product"
            )

            if not product:
                raise ValueError(
                    "Product is required."
                )

            product_id = str(
                product.id
            )

            if product_id in product_ids:
                raise ValueError(
                    "Duplicate product in fulfilment."
                )

            product_ids.add(
                product_id
            )

            order_item = order_items.get(
                product_id
            )

            if not order_item:
                raise ValueError(
                    f"Product {product.sku} "
                    "is not part of this sales order."
                )

            quantity_to_fulfill = (
                SalesOrderService._to_decimal(
                    raw_item.get(
                        "quantity"
                    ),
                    "fulfilment quantity",
                )
            )

            if quantity_to_fulfill <= 0:
                raise ValueError(
                    "Fulfilment quantity must be "
                    "greater than zero."
                )

            remaining_quantity = (
                order_item.quantity
                - order_item.fulfilled_quantity
            )

            if (
                quantity_to_fulfill
                > remaining_quantity
            ):
                raise ValueError(
                    f"Cannot fulfil more than remaining "
                    f"quantity for product "
                    f"{product.sku}. "
                    f"Remaining: {remaining_quantity}."
                )

            inventory = (
                InventoryRepository
                .get_by_product_and_warehouse(
                    organization=organization,
                    product=product,
                    warehouse=sales_order.warehouse,
                )
            )

            if not inventory:
                raise ValueError(
                    f"Inventory not found for "
                    f"product {product.sku}."
                )

            # This SO's units should already
            # be represented in reserved stock.
            if (
                inventory.reserved_quantity
                < quantity_to_fulfill
            ):
                raise ValueError(
                    f"Insufficient reserved inventory "
                    f"for product {product.sku}. "
                    f"Required: {quantity_to_fulfill}, "
                    f"Reserved: "
                    f"{inventory.reserved_quantity}."
                )

            if (
                inventory.quantity
                < quantity_to_fulfill
            ):
                raise ValueError(
                    f"Insufficient physical inventory "
                    f"for product {product.sku}."
                )

            fulfilments.append(
                {
                    "product": product,
                    "order_item": order_item,
                    "inventory": inventory,
                    "quantity":
                        quantity_to_fulfill,
                }
            )

        # ---------------------------------------------
        # EXECUTE FULFILMENT
        # ---------------------------------------------

        for fulfilment in fulfilments:

            inventory = fulfilment[
                "inventory"
            ]

            order_item = fulfilment[
                "order_item"
            ]

            quantity_to_fulfill = (
                fulfilment["quantity"]
            )

            quantity_before = (
                inventory.quantity
            )

            reserved_before = (
                inventory.reserved_quantity
            )

            quantity_after = (
                quantity_before
                - quantity_to_fulfill
            )

            reserved_after = (
                reserved_before
                - quantity_to_fulfill
            )

            # Physical stock decreases.
            inventory = (
                InventoryRepository
                .update_quantity(
                    inventory=inventory,
                    quantity=quantity_after,
                )
            )

            # Reservation is consumed.
            inventory = (
                InventoryRepository
                .update_reserved_quantity(
                    inventory=inventory,
                    reserved_quantity=(
                        reserved_after
                    ),
                )
            )

            order_item.fulfilled_quantity += (
                quantity_to_fulfill
            )

            StockMovementService.create_movement(
                user=user,
                organization=organization,
                inventory=inventory,
                movement_type="STOCK_OUT",
                quantity=-quantity_to_fulfill,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                reserved_before=reserved_before,
                reserved_after=reserved_after,
                reference_type="SALES_ORDER",
                reference_id=(
                    sales_order.so_number
                ),
                notes=(
                    notes.strip()
                    or (
                        "Stock dispatched for "
                        f"sales order "
                        f"{sales_order.so_number}"
                    )
                ),
            )

        # ---------------------------------------------
        # DETERMINE NEW SALES ORDER STATUS
        # ---------------------------------------------

        all_fulfilled = all(
            item.fulfilled_quantity
            >= item.quantity
            for item in sales_order.items
        )

        if all_fulfilled:
            new_status = "FULFILLED"
            fulfilled_at = datetime.utcnow()

        else:
            new_status = "PARTIALLY_FULFILLED"
            fulfilled_at = None

        return (
            SalesOrderRepository
            .update_fulfilled_quantities(
                sales_order=sales_order,
                items=sales_order.items,
                status=new_status,
                fulfilled_at=fulfilled_at,
            )
        )