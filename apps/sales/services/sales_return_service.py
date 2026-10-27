from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from apps.authorization.services import (
    AuthorizationService,
)

from apps.sales.models import (
    SalesReturnItem,
)

from apps.sales.repositories.sales_return_repository import (
    SalesReturnRepository,
)
from apps.inventory.services.inventory_service import (
    InventoryService,
)

class SalesReturnService:

    VALID_STATUSES = {
        "DRAFT",
        "CONFIRMED",
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

        if (
            user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong to "
                "this organization."
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

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            raise ValueError(
                f"Invalid {field_name}."
            )

    @staticmethod
    def _generate_return_number():
        return (
            "SR-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _get_invoice_item(
        invoice,
        product,
    ):
        for item in invoice.items:
            if (
                item.product.id
                == product.id
            ):
                return item

        return None

    @staticmethod
    def _get_order_item(
        sales_order,
        product,
    ):
        for item in sales_order.items:
            if (
                item.product.id
                == product.id
            ):
                return item

        return None

    @staticmethod
    def _confirmed_returned_quantity(
        *,
        organization,
        invoice,
        product,
    ):
        confirmed_returns = (
            SalesReturnRepository
            .list_confirmed_by_invoice(
                organization=organization,
                invoice=invoice,
            )
        )

        return sum(
            (
                item.quantity
                for sales_return
                in confirmed_returns
                for item
                in sales_return.items
                if (
                    item.product.id
                    == product.id
                )
            ),
            Decimal("0"),
        )

    @staticmethod
    def create_return(
        *,
        user,
        organization,
        invoice,
        items,
        return_date=None,
        reason="",
        notes="",
    ):
        SalesReturnService._check_permission(
            user,
            "sales_returns.create",
        )

        SalesReturnService._check_organization(
            user,
            organization,
        )

        if not invoice:
            raise ValueError(
                "Invoice is required."
            )

        if (
            invoice.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Invoice does not belong "
                "to this organization."
            )

        if not invoice.sales_order:
            raise ValueError(
                "Invoice has no sales order."
            )

        sales_order = invoice.sales_order

        if (
            sales_order.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Sales order does not belong "
                "to this organization."
            )

        if (
            invoice.customer.id
            != sales_order.customer.id
        ):
            raise ValueError(
                "Invoice customer does not match "
                "sales order customer."
            )

        if invoice.status == "CANCELLED":
            raise ValueError(
                "Cannot create a return "
                "for a cancelled invoice."
            )

        if sales_order.status not in {
            "PARTIALLY_FULFILLED",
            "FULFILLED",
        }:
            raise ValueError(
                "Sales order has no fulfilled "
                "goods available for return."
            )

        if not items:
            raise ValueError(
                "At least one return item "
                "is required."
            )

        if not isinstance(
            items,
            list,
        ):
            raise ValueError(
                "items must be a list."
            )

        return_date = (
            return_date
            or datetime.utcnow()
        )

        seen_products = set()
        return_items = []

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")
        total_amount = Decimal("0")

        for item_data in items:
            product = item_data.get(
                "product"
            )

            if not product:
                raise ValueError(
                    "Return item product "
                    "is required."
                )

            product_id = str(
                product.id
            )

            if product_id in seen_products:
                raise ValueError(
                    "Duplicate product in "
                    "sales return."
                )

            seen_products.add(
                product_id
            )

            if (
                product.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Product does not belong "
                    "to this organization."
                )

            invoice_item = (
                SalesReturnService
                ._get_invoice_item(
                    invoice,
                    product,
                )
            )

            if not invoice_item:
                raise ValueError(
                    "Product does not exist "
                    "on the invoice."
                )

            order_item = (
                SalesReturnService
                ._get_order_item(
                    sales_order,
                    product,
                )
            )

            if not order_item:
                raise ValueError(
                    "Product does not exist "
                    "on the sales order."
                )

            quantity = (
                SalesReturnService
                ._to_decimal(
                    item_data.get(
                        "quantity"
                    ),
                    "return quantity",
                )
            )

            if quantity <= 0:
                raise ValueError(
                    "Return quantity must "
                    "be greater than zero."
                )

            already_returned = (
                SalesReturnService
                ._confirmed_returned_quantity(
                    organization=organization,
                    invoice=invoice,
                    product=product,
                )
            )

            returnable_quantity = (
                order_item.fulfilled_quantity
                - already_returned
            )

            if returnable_quantity <= 0:
                raise ValueError(
                    "No remaining quantity "
                    "is available for return."
                )

            if (
                quantity
                > returnable_quantity
            ):
                raise ValueError(
                    "Return quantity exceeds "
                    "remaining fulfilled quantity."
                )

            unit_price = (
                invoice_item.unit_price
            )

            tax_rate = (
                invoice_item.tax_rate
            )

            discount = (
                invoice_item.discount
            )

            invoice_quantity = (
                invoice_item.quantity
            )

            if invoice_quantity <= 0:
                raise ValueError(
                    "Invoice item quantity "
                    "is invalid."
                )

            line_subtotal = (
                unit_price
                * quantity
            )

            proportional_discount = (
                discount
                * quantity
                / invoice_quantity
            )

            taxable_amount = (
                line_subtotal
                - proportional_discount
            )

            if taxable_amount < 0:
                taxable_amount = Decimal("0")

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
                SalesReturnItem(
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    discount=(
                        proportional_discount
                    ),
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

            discount_amount += (
                proportional_discount
            )

            tax_amount += line_tax

            total_amount += line_total

        sales_return = (
            SalesReturnRepository
            .create_return(
                organization=organization,
                return_number=(
                    SalesReturnService
                    ._generate_return_number()
                ),
                sales_order=sales_order,
                invoice=invoice,
                customer=invoice.customer,
                warehouse=(
                    sales_order.warehouse
                ),
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

        return sales_return

    @staticmethod
    def confirm_return(
        *,
        user,
        organization,
        sales_return,
    ):
        SalesReturnService._check_permission(
            user,
            "sales_returns.confirm",
        )

        SalesReturnService._check_organization(
            user,
            organization,
        )

        if not sales_return:
            raise ValueError(
                "Sales return is required."
            )

        if (
            sales_return.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Sales return does not belong "
                "to this organization."
            )

        if sales_return.status != "DRAFT":
            raise ValueError(
                "Only draft sales returns "
                "can be confirmed."
            )

        invoice = sales_return.invoice
        sales_order = sales_return.sales_order

        if invoice.status == "CANCELLED":
            raise ValueError(
                "Cannot confirm a return "
                "for a cancelled invoice."
            )

        if sales_order.status not in {
            "PARTIALLY_FULFILLED",
            "FULFILLED",
        }:
            raise ValueError(
                "Sales order has no fulfilled "
                "goods available for return."
            )

        if (
            invoice.customer.id
            != sales_return.customer.id
        ):
            raise ValueError(
                "Sales return customer does "
                "not match invoice customer."
            )

        if (
            sales_order.customer.id
            != sales_return.customer.id
        ):
            raise ValueError(
                "Sales return customer does "
                "not match sales order customer."
            )

        if (
            sales_order.warehouse.id
            != sales_return.warehouse.id
        ):
            raise ValueError(
                "Sales return warehouse does "
                "not match sales order warehouse."
            )

        #
        # Revalidate every return item BEFORE
        # changing any inventory.
        #
        for return_item in sales_return.items:
            order_item = (
                SalesReturnService
                ._get_order_item(
                    sales_order,
                    return_item.product,
                )
            )

            if not order_item:
                raise ValueError(
                    "Return product does not exist "
                    "on the sales order."
                )

            invoice_item = (
                SalesReturnService
                ._get_invoice_item(
                    invoice,
                    return_item.product,
                )
            )

            if not invoice_item:
                raise ValueError(
                    "Return product does not exist "
                    "on the invoice."
                )

            already_returned = (
                SalesReturnService
                ._confirmed_returned_quantity(
                    organization=organization,
                    invoice=invoice,
                    product=return_item.product,
                )
            )

            remaining_returnable = (
                order_item.fulfilled_quantity
                - already_returned
            )

            if return_item.quantity <= 0:
                raise ValueError(
                    "Return quantity must be "
                    "greater than zero."
                )

            if (
                return_item.quantity
                > remaining_returnable
            ):
                raise ValueError(
                    "Return quantity exceeds "
                    "remaining fulfilled quantity."
                )

        #
        # All validation passed.
        # Now restore physical inventory.
        #
        for return_item in sales_return.items:
            InventoryService.record_business_movement(
                user=user,
                organization=organization,
                product=return_item.product,
                warehouse=sales_return.warehouse,
                quantity_change=(
                    return_item.quantity
                ),
                movement_type="SALES_RETURN",
                reference_type="SALES_RETURN",
                reference_id=(
                    sales_return.return_number
                ),
                notes=(
                    "Customer sales return "
                    f"{sales_return.return_number}"
                ),
            )

        sales_return = (
            SalesReturnRepository
            .update_status(
                sales_return=sales_return,
                status="CONFIRMED",
                confirmed_at=datetime.utcnow(),
            )
        )

        return sales_return

    @staticmethod
    def cancel_return(
        *,
        user,
        organization,
        sales_return,
    ):
        """
        Cancel a draft sales return.

        Confirmed returns cannot be cancelled
        directly because confirmation has already
        restored inventory.
        """

        SalesReturnService._check_permission(
            user,
            "sales_returns.cancel",
        )

        SalesReturnService._check_organization(
            user,
            organization,
        )

        if not sales_return:
            raise ValueError(
                "Sales return is required."
            )

        if (
            sales_return.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Sales return does not belong "
                "to this organization."
            )

        if (
            sales_return.status
            ==
            "CANCELLED"
        ):
            raise ValueError(
                "Sales return is already "
                "cancelled."
            )

        if (
            sales_return.status
            ==
            "CONFIRMED"
        ):
            raise ValueError(
                "Confirmed sales returns cannot "
                "be cancelled directly because "
                "inventory has already been "
                "restored."
            )

        if (
            sales_return.status
            !=
            "DRAFT"
        ):
            raise ValueError(
                "Only draft sales returns "
                "can be cancelled."
            )

        return (
            SalesReturnRepository
            .update_status(
                sales_return=sales_return,
                status="CANCELLED",
                cancelled_at=(
                    datetime.utcnow()
                ),
            )
        )